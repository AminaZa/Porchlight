"""Triage — classify one report and produce its redacted, indexable sentence.

No tools. This is typed extraction from a single short text, which structured
output does more reliably than a tool round-trip, and it is why this stage runs
on Haiku rather than something larger.
"""

from __future__ import annotations

from strands import Agent

from src.models import RawReport, TriageResult
from src.prompts import TRIAGE
from src.provider import get_model


def _agent() -> Agent:
    # A fresh Agent per report so no conversation history carries across
    # reports. The model object is cached in provider.get_model, and prompt
    # caching is keyed server-side on the prompt prefix bytes, so a new Agent
    # instance costs nothing and still reads the cached prefix.
    return Agent(
        model=get_model("triage"),
        system_prompt=TRIAGE,
        structured_output_model=TriageResult,
        callback_handler=None,  # keep demo output clean
        name="porchlight-triage",
    )


def triage(raw: RawReport) -> TriageResult:
    """Classify and redact one raw report."""
    prompt = (
        f"Zone: {raw.zone}\n"
        f"Time: {raw.timestamp.isoformat()}\n"
        f"Report: {raw.text}"
    )
    result = _agent()(prompt).structured_output
    if result is None:
        raise RuntimeError("triage returned no structured output")
    return result
