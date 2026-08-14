"""Escalation — the judgment call, and the only stage worth Opus.

The decision lives in the agent's reasoning under its system prompt, never in
an `if cluster_size > 3` branch. Thresholds reach it as *evidence* and it
weighs them. `EscalationDecision.reasoning` is required and is shown on screen,
which is the difference between an agent and a cron job.

It holds one read-only tool so it can look deeper before deciding. It does not
hold the trigger — see tools/alerts.py for why dispatch is the pipeline's job.
"""

from __future__ import annotations

from strands import Agent

from src.models import CorrelationSummary, EscalationDecision, TriagedReport
from src.prompts import ESCALATION
from src.provider import get_model
from src.tools.storage import get_zone_history


def _agent() -> Agent:
    return Agent(
        model=get_model("escalation"),
        system_prompt=ESCALATION,
        tools=[get_zone_history],
        structured_output_model=EscalationDecision,
        callback_handler=None,
        name="porchlight-escalation",
    )


def _evidence(report: TriagedReport, summary: CorrelationSummary) -> str:
    if summary.cluster_size <= 1:
        related = "Nothing else logged describes this situation."
    else:
        zones = ", ".join(summary.zones_involved)
        related = (
            f"Reports describing the same situation: {summary.cluster_size}\n"
            f"Separate people who reported it: {summary.distinct_reporters}\n"
            f"Spread over: {summary.time_span_hours:.1f} hours\n"
            f"Zones involved ({len(summary.zones_involved)}): {zones}"
        )

    return (
        f"New report\n"
        f"  Zone: {report.zone}\n"
        f"  Time: {report.timestamp.isoformat()}\n"
        f"  Type: {report.report_type} (severity {report.severity}/5)\n"
        f"  Summary: {report.summary}\n\n"
        f"Correlation evidence\n"
        f"  {related}\n\n"
        f"Rate for this zone against its own history\n"
        f"  Anomaly score: {summary.anomaly_score:.2f}\n\n"
        f"What the correlation stage made of it\n"
        f"  {summary.assessment}"
    )


def decide(report: TriagedReport, summary: CorrelationSummary) -> EscalationDecision:
    """Decide whether this report warrants waking a person."""
    result = _agent()(_evidence(report, summary)).structured_output
    if result is None:
        raise RuntimeError("escalation returned no structured output")

    # A silent log has no recipient and no message. The schema allows the
    # fields to be populated; the record should not be.
    if result.action == "silent_log":
        result.message = ""
    return result
