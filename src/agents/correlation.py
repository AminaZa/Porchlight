"""Correlation — find whether anything already logged is the same situation.

This is where the real tool surface lives: the agent's judgment determines
which lookups to make and how wide to search, which is exactly the case where
giving a model tools earns its keep.

It returns ids and prose. It does not return counts — the pipeline counts those
from the ids, so the evidence reaching the escalation stage is measured rather
than asserted. See models.py.
"""

from __future__ import annotations

from strands import Agent

from src.models import CorrelationResult, TriagedReport
from src.prompts import CORRELATION
from src.provider import get_model
from src.tools.anomaly import check_baseline_deviation
from src.tools.storage import get_zone_history
from src.tools.vectors import semantic_search


def _agent() -> Agent:
    return Agent(
        model=get_model("correlation"),
        system_prompt=CORRELATION,
        tools=[semantic_search, check_baseline_deviation, get_zone_history],
        structured_output_model=CorrelationResult,
        callback_handler=None,
        name="porchlight-correlation",
    )


def correlate(report: TriagedReport) -> CorrelationResult:
    """Gather correlation evidence for one freshly-triaged report."""
    prompt = (
        f"A new report has just come in.\n\n"
        f"Report id: {report.report_id}\n"
        f"Zone: {report.zone}\n"
        f"Time: {report.timestamp.isoformat()}\n"
        f"Type: {report.report_type}\n"
        f"Summary: {report.summary}\n\n"
        f"Does anything already logged describe the same ongoing situation? "
        f"Do not include {report.report_id} itself in related_report_ids."
    )
    result = _agent()(prompt).structured_output
    if result is None:
        raise RuntimeError("correlation returned no structured output")

    # The agent is told not to, but a self-reference would inflate cluster_size
    # by one and there is no reason to let a prompt be the only guard.
    result.related_report_ids = [
        rid for rid in result.related_report_ids if rid != report.report_id
    ]
    return result
