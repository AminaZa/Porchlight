"""Offline stand-ins for the three model calls.

    python demo/run_demo.py --offline

Lets the pipeline run end to end with no AWS account and no spend, so the
system can be exercised, developed against, and shown on a laptop before
Bedrock credentials exist.

--------------------------------------------------------------------------
THESE ARE NOT THE AGENTS. Offline mode replaces every model call with a
hand-written fixture or a hard-coded rule. It demonstrates the *pipeline*;
it demonstrates nothing whatsoever about the model's judgment, which is the
entire point of the product.

Do not record offline output for the demo video, and do not present it as
the agent working. Every surface it touches says OFFLINE for that reason:
the terminal banner, each printed line, and a band across the top of the
rendered HTML report.
--------------------------------------------------------------------------

What is still real, and worth watching even here: storage, ChromaDB
embedding and retrieval, the per-zone anomaly detector, evidence
computation, alert suppression, and the renderer. The four differently
worded cluster reports are found by genuine semantic search — that part
does not depend on a model call.

--------------------------------------------------------------------------
WHAT OFFLINE MODE CANNOT SHOW, AND WHY IT MATTERS

The near-miss never correlates here, so the run shows the alert and the
single-reporter decline but not the three-zone decline. That is not a bug
in this file and it is not fixable by tuning the threshold below. Measured
across the seed set:

    within the genuine cluster      similarity 0.708 - 0.814
    within the near-miss            similarity 0.436 - 0.456
    near-miss -> an unrelated report            0.576

The near-miss reports resemble each other LESS than one of them resembles
a completely unrelated report about a car driving past some driveways.
Sweeping the threshold does not rescue it: at 0.45 it picks up 2 correct
near-miss links and 20 incorrect ones; at 0.50 and above it picks up none.

That is the clearest evidence in the project that the correlation agent is
doing something a similarity score cannot. Separating "three people
described loitering in three different zones over three weeks" from "these
two sentences both mention driveways" requires reading them and weighing
where and when, which is the entire reason there is an agent here and not
an `if similarity > x` branch.

So the near-miss is a demonstration of the model's judgment, and a stub
that has no judgment cannot demonstrate it. Run against Bedrock for that.
--------------------------------------------------------------------------
"""

from __future__ import annotations

import json
from pathlib import Path

from src.models import (
    CorrelationResult,
    CorrelationSummary,
    EscalationDecision,
    RawReport,
    TriageResult,
    TriagedReport,
)
from src.tools import vectors

FIXTURES = Path(__file__).parent / "offline_fixtures.json"

BANNER = """
  ┌──────────────────────────────────────────────────────────────────┐
  │  OFFLINE MODE — the three model calls are stubbed.               │
  │                                                                  │
  │  Retrieval, the anomaly detector, evidence counting, suppression │
  │  and rendering are all real. The judgment is not: escalation is  │
  │  a hard-coded rule here, not Opus reasoning over the evidence.   │
  │                                                                  │
  │  The near-miss will NOT appear. Those three reports resemble     │
  │  each other less (0.44) than one resembles an unrelated report   │
  │  (0.58), so no threshold recovers them — only reading them does. │
  │                                                                  │
  │  Do not record this for the video.                               │
  └──────────────────────────────────────────────────────────────────┘
"""

# Above this cosine similarity the crude stub treats two reports as the same
# situation.
#
# Chosen from a sweep over the seed set, not by feel. At 0.62 the genuine
# cluster and the single-reporter run both link cleanly with only two
# cross-group links in the whole set. Lowering it to catch the near-miss
# costs far more than it buys: 0.45 adds 2 correct links and 20 wrong ones.
# See the note above — a single threshold is the wrong instrument, and that
# is the point.
SIMILARITY_THRESHOLD = 0.62


def _load() -> dict[str, list]:
    data = json.loads(FIXTURES.read_text(encoding="utf-8"))
    return data["summaries"]


_SUMMARIES = _load()


def triage(raw: RawReport) -> TriageResult:
    """Look up a hand-written summary. No model involved."""
    key = f"{raw.reporter_id}|{raw.timestamp.isoformat()}"
    entry = _SUMMARIES.get(key)
    if entry is None:
        raise KeyError(
            f"No offline fixture for {key}. Offline mode only covers the seed "
            f"set; add an entry to {FIXTURES.name} or run against Bedrock."
        )
    report_type, severity, summary = entry
    return TriageResult(report_type=report_type, severity=severity, summary=summary)


def correlate(report: TriagedReport) -> CorrelationResult:
    """Real semantic search, then a similarity cutoff instead of judgment."""
    hits = vectors.search(report.summary, limit=8, exclude_ids=[report.report_id])
    related = [h["report_id"] for h in hits if h["similarity"] >= SIMILARITY_THRESHOLD]

    if not related:
        assessment = "Nothing already logged resembles this closely enough to connect."
    else:
        best = max(h["similarity"] for h in hits if h["report_id"] in related)
        assessment = (
            f"{len(related)} earlier report(s) match above {SIMILARITY_THRESHOLD:.2f} "
            f"similarity (closest {best:.2f}). Threshold only — no reading of the "
            f"reports was involved."
        )
    return CorrelationResult(related_report_ids=related, assessment=assessment)


def decide(report: TriagedReport, summary: CorrelationSummary) -> EscalationDecision:
    """A hard-coded rule standing in for the judgment. This is the stub that
    matters least and misleads most, which is why offline output is labelled."""
    corroborated = summary.distinct_reporters >= 3
    recent = summary.time_span_hours <= 48
    local = len(summary.zones_involved) == 1
    unusual = summary.anomaly_score >= 2.0
    alert = summary.cluster_size >= 3 and corroborated and recent and local and unusual

    if alert:
        message = (
            f"Several neighbours have separately reported activity around "
            f"{report.zone.lower()} in the last day or so. Worth someone taking a "
            f"look before the weekend."
        )
        reasoning = (
            f"{summary.cluster_size} reports from {summary.distinct_reporters} "
            f"different people, all in one zone, inside "
            f"{summary.time_span_hours:.0f} hours, in a place that normally sees "
            f"far less (z={summary.anomaly_score:.1f}). [rule, not judgment]"
        )
    else:
        message = ""
        n = summary.distinct_reporters
        zones = len(summary.zones_involved)
        days = summary.time_span_hours / 24

        # Name the condition that actually decided it, most decisive first.
        # Reporting "too few reporters" for a cluster whose real problem is a
        # three-week span explains nothing and teaches the reader the wrong
        # rule about how the system thinks.
        if summary.cluster_size <= 1:
            reasoning = "Nothing else describes this situation. Logged."
        elif n == 1:
            reasoning = (
                f"{summary.cluster_size} similar reports, all from the same "
                f"person. One neighbour's repeated concern is not corroboration."
            )
        elif not recent and not local:
            reasoning = (
                f"{summary.cluster_size} similar reports, but spread over "
                f"{days:.0f} days and {zones} zones. Things that resemble each "
                f"other at that distance are usually separate events."
            )
        elif not recent:
            reasoning = (
                f"{summary.cluster_size} similar reports, but {days:.0f} days "
                f"apart. Too far apart to be one ongoing situation."
            )
        elif not local:
            reasoning = (
                f"{summary.cluster_size} similar reports across {zones} "
                f"different zones. Not one place, so not one situation."
            )
        elif not corroborated:
            reasoning = (
                f"{summary.cluster_size} similar reports but only {n} people "
                f"reporting. Not enough independent corroboration to wake anyone."
            )
        else:
            reasoning = (
                f"Correlated, but this zone's rate is not unusual for it "
                f"(z={summary.anomaly_score:.1f})."
            )
        reasoning += " [rule, not judgment]"

    return EscalationDecision(
        action="alert" if alert else "silent_log",
        urgency="medium" if alert else "low",
        audience="block_captain",
        message=message,
        reasoning=reasoning,
    )


def install() -> None:
    """Point the pipeline at these stubs instead of the agents."""
    from src import pipeline

    pipeline.triage = triage
    pipeline.correlate = correlate
    pipeline.decide = decide
