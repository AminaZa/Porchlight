"""Alert dispatch and the silent log.

**Deviation from the plan, flagged:** the plan gave the escalation agent
`draft_alert` and `send_alert` as tools. They are plain functions called by the
pipeline instead, for the same reason persistence is (§3): `EscalationDecision`
already carries action, urgency, audience, and the message text — every
argument `send_alert` would take. Having the agent then call a tool with those
same values adds a round-trip that can disagree with the decision it just made,
and creates two ways for an alert to be sent or missed.

The agent decides. The pipeline dispatches. The human approves.

The escalation agent keeps `get_zone_history` so it can look deeper before
deciding; it just doesn't hold the trigger.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path

from src.models import CorrelationSummary, EscalationDecision, TriagedReport

ALERT_LOG = Path(os.environ.get("FNA_ALERT_LOG", "alerts.log"))

# Palette from BRANDING.md. Amber marks escalation and nothing else.
_LAMP = "\033[38;5;215m"
_DIM = "\033[38;5;103m"
_QUIET = "\033[38;5;60m"
_BOLD = "\033[1m"
_OFF = "\033[0m"


def _colour_ok() -> bool:
    return sys.stdout.isatty() and os.environ.get("NO_COLOR") is None


def _paint(text: str, colour: str) -> str:
    return f"{colour}{text}{_OFF}" if _colour_ok() else text


def requires_approval() -> bool:
    """Whether a human must approve before an alert is dispatched.

    Off for the demo so a 38-report run isn't 38 prompts. **On for any real
    deployment** — see IMPLEMENTATION_PLAN.md §4.3. The agent's job is to
    notice and draft; a person decides to send.
    """
    return os.environ.get("FNA_REQUIRE_APPROVAL", "").strip() in {"1", "true", "yes"}


def render_alert(
    decision: EscalationDecision, report: TriagedReport, summary: CorrelationSummary
) -> str:
    """The alert as a recipient would see it, plus the evidence line."""
    evidence = (
        f"cluster {summary.cluster_size} · "
        f"{summary.distinct_reporters} reporters · "
        f"{summary.time_span_hours:.0f}h · "
        f"z={summary.anomaly_score:.1f}"
    )
    return (
        f"▲ Pattern — {report.zone}\n"
        f"{decision.message}\n"
        f"{evidence} · to {decision.audience.replace('_', ' ')}"
    )


def _confirm(body: str) -> bool:
    print(_paint("\n  An alert is ready to send:\n", _LAMP))
    print("\n".join("    " + line for line in body.splitlines()))
    try:
        answer = input(_paint("\n  Send it? [y/N] ", _LAMP)).strip().lower()
    except EOFError:
        # Non-interactive with approval required: refuse rather than send
        # something nobody agreed to.
        print(_paint("  No terminal to confirm on — not sent.", _DIM))
        return False
    return answer in {"y", "yes"}


def send_alert(
    decision: EscalationDecision, report: TriagedReport, summary: CorrelationSummary
) -> bool:
    """Dispatch an alert. Returns whether it was actually sent.

    Writes to the console and appends to the alert log. Real dispatch (SMS,
    Discord) is phase 2 — the point of this pass is the judgment, not the
    transport.
    """
    body = render_alert(decision, report, summary)

    if requires_approval() and not _confirm(body):
        write_log(report, decision, summary, note="alert drafted, approval declined")
        return False

    print()
    for line in body.splitlines():
        print("  " + _paint(line, _LAMP))
    print()

    ALERT_LOG.parent.mkdir(parents=True, exist_ok=True)
    with ALERT_LOG.open("a", encoding="utf-8") as fh:
        fh.write(f"--- {datetime.now().astimezone().isoformat()} ---\n{body}\n\n")
    return True


def write_log(
    report: TriagedReport,
    decision: EscalationDecision,
    summary: CorrelationSummary,
    note: str = "",
) -> None:
    """The silent log — the common case, and the one the product is about."""
    del summary, note  # persisted by storage.record_decision; kept for symmetry
    if decision.action == "silent_log":
        return


def format_line(
    index: int,
    total: int,
    report: TriagedReport,
    decision: EscalationDecision,
    summary: CorrelationSummary,
    suppressed: bool = False,
) -> str:
    """One demo line per report. This is most of what the video shows."""
    prefix = f"[{index:02d}/{total}]"
    zone = report.zone[:24].ljust(24)
    kind = report.report_type.ljust(11)

    if decision.action == "alert":
        return _paint(f"{prefix}  {zone} {kind} ▲  ALERT", _LAMP + _BOLD)

    if suppressed:
        return _paint(
            f"{prefix}  {zone} {kind} ·  logged (cluster already alerted)", _DIM
        )

    if summary.cluster_size > 1:
        detail = (
            f"{summary.cluster_size} similar · "
            f"{summary.distinct_reporters} reporters · "
            f"{summary.time_span_hours:.0f}h · "
            f"{len(summary.zones_involved)} zone(s)"
        )
        return _paint(f"{prefix}  {zone} {kind} ·  declined", _DIM) + "\n" + _paint(
            f"           {detail}", _QUIET
        )

    return _paint(f"{prefix}  {zone} {kind} ·  silent log", _QUIET)
