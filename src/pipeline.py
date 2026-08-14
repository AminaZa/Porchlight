"""Orchestration: triage → persist → correlate → escalate → dispatch.

A sequential workflow rather than a swarm or a handoff graph. Three agents,
three prompts, three tool sets, but no routing decision to debug — the brief
names multi-agent debugging as the project's biggest schedule risk, and there
is no routing choice here to justify paying that cost.

Two things deliberately do not live in an agent:

*Persistence* runs here, between triage and correlation. An agent that skips a
write leaves the report invisible to every later search, the cluster comes back
one short, escalation correctly declines, and nothing raises.

*The correlation counts* are computed here from the ids the agent returned.
``distinct_reporters`` is a safety control, and a control a model self-reports
is not a control.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from src.agents.correlation import correlate
from src.agents.escalation import decide
from src.agents.triage import triage
from src.models import (
    CorrelationSummary,
    EscalationDecision,
    RawReport,
    TriagedReport,
)
from src.tools import alerts, anomaly, storage, vectors


class StageError(RuntimeError):
    """A pipeline stage failed. Names the stage, because 'it broke' is useless
    when three models and four tools are involved."""

    def __init__(self, stage: str, cause: Exception):
        super().__init__(f"{stage} stage failed: {cause}")
        self.stage = stage
        self.cause = cause


@dataclass
class Processed:
    """Everything one report produced. What the demo and renderer read."""

    report: TriagedReport
    summary: CorrelationSummary
    decision: EscalationDecision
    sent: bool = False
    suppressed: bool = False

    @property
    def outcome(self) -> str:
        """One of: alert, suppressed, declined, silent."""
        if self.decision.action == "alert" and self.sent:
            return "alert"
        if self.decision.action == "alert" and self.suppressed:
            return "suppressed"
        if self.summary.cluster_size > 1:
            return "declined"
        return "silent"


def _stage(name: str, fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except Exception as exc:  # noqa: BLE001 - re-raised with the stage attached
        raise StageError(name, exc) from exc


def build_summary(
    report: TriagedReport, related_ids: list[str], assessment: str
) -> CorrelationSummary:
    """Turn the agent's ids into counted evidence.

    Every number here is derived from storage. The agent contributed the ids
    and the prose; it did not contribute a single figure the next stage weighs.
    """
    related = storage.get_reports(related_ids)
    cluster = [report] + related

    timestamps = [r.timestamp for r in cluster]
    span_hours = (max(timestamps) - min(timestamps)).total_seconds() / 3600.0

    deviation = anomaly.measure(
        report.zone, storage.zone_timestamps(report.zone), report.timestamp
    )

    return CorrelationSummary(
        cluster_size=len(cluster),
        distinct_reporters=len({r.reporter_id for r in cluster}),
        time_span_hours=round(span_hours, 2),
        zones_involved=sorted({r.zone for r in cluster}),
        anomaly_score=deviation.z_score,
        related_report_ids=[r.report_id for r in related],
        assessment=assessment,
    )


def process_report(raw: RawReport) -> Processed:
    """Run one report all the way through."""
    triaged_result = _stage("triage", triage, raw)
    report = TriagedReport.from_raw(raw, triaged_result)

    # Persist before correlating: the report must be searchable by the time
    # anything downstream looks, and later reports must be able to find it.
    _stage("persist", storage.store_report, report, raw.text)
    _stage("index", vectors.embed_and_index, report)

    correlation = _stage("correlation", correlate, report)
    summary = _stage(
        "evidence",
        build_summary,
        report,
        correlation.related_report_ids,
        correlation.assessment,
    )

    decision = _stage("escalation", decide, report, summary)

    sent = False
    suppressed = False
    if decision.action == "alert":
        covered = [report.report_id, *summary.related_report_ids]
        if storage.cluster_already_alerted(covered):
            # This situation has already woken someone. Log it instead of
            # sending a second alert about the same thing.
            suppressed = True
            # Extend the coverage to this report too. It is part of the
            # situation the earlier alert was about, so anything reading
            # coverage — the renderer deciding which nodes are lit, the card
            # picker deciding which decline is worth showing — has to see it
            # that way. Without this the graph draws a four-report cluster as
            # three, and the suppressed duplicate masquerades as a genuine
            # decline.
            storage.mark_cluster_alerted(covered, alert_key=report.report_id)
        else:
            sent = _stage("dispatch", alerts.send_alert, decision, report, summary)
            if sent:
                storage.mark_cluster_alerted(covered, alert_key=report.report_id)

    _stage(
        "record", storage.record_decision, report.report_id, decision, summary, suppressed
    )

    return Processed(
        report=report,
        summary=summary,
        decision=decision,
        sent=sent,
        suppressed=suppressed,
    )


def submit(text: str, zone: str, reporter_id: str, when: datetime | None = None) -> Processed:
    """Convenience entry point for the CLI and for tests."""
    storage.init_db()
    return process_report(
        RawReport(
            text=text,
            zone=zone,
            reporter_id=reporter_id,
            timestamp=when or datetime.now().astimezone(),
        )
    )
