"""Triage — classify one report and produce its redacted, indexable sentence.

No tools. This is typed extraction from a single short text, which structured
output does more reliably than a tool round-trip, and it is why this stage runs
on Haiku rather than something larger.

This is the only stage that ever sees a reporter's raw words, which makes it
the one place person-identifying detail can enter the system. It runs under
``RedactionGuard`` — see src/guards.py — so a summary that still describes a
person is discarded and regenerated before the pipeline, storage, or the index
ever see it.
"""

from __future__ import annotations

from strands import Agent

from src.guards import RedactionGuard
from src.models import RawReport, TriageResult
from src.prompts import TRIAGE
from src.provider import get_model


def _agent(guard: RedactionGuard) -> Agent:
    # A fresh Agent per report so no conversation history carries across
    # reports. The model object is cached in provider.get_model, and prompt
    # caching is keyed server-side on the prompt prefix bytes, so a new Agent
    # instance costs nothing and still reads the cached prefix.
    #
    # The guard is passed in rather than constructed here so the caller can
    # read what it caught after the fact.
    return Agent(
        model=get_model("triage"),
        system_prompt=TRIAGE,
        structured_output_model=TriageResult,
        callback_handler=None,  # keep demo output clean
        hooks=[guard],
        name="porchlight-triage",
    )


def triage(raw: RawReport) -> TriageResult:
    """Classify and redact one raw report.

    Raises ``guards.RedactionViolation`` if the model keeps returning a summary
    that identifies a person. Failing the report is the intended outcome — the
    alternative is indexing a description of somebody.
    """
    prompt = (
        f"Zone: {raw.zone}\n"
        f"Time: {raw.timestamp.isoformat()}\n"
        f"Report: {raw.text}"
    )
    guard = RedactionGuard(label="triage")
    result = _agent(guard)(prompt).structured_output
    if result is None:
        raise RuntimeError("triage returned no structured output")
    return result
