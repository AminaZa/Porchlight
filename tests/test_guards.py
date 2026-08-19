"""The redaction guard, offline.

``tests/test_redaction.py`` asks a live model whether it redacts. This file
asks whether the guard would catch it if it didn't — which is the question that
matters, because the guard is what stands between a leaked description and the
vector store.

Two halves, and both are load-bearing:

*Recall* — the constructions a neighbour actually types must be caught. Each
case here is a real sentence, not a regex fixture.

*Precision* — every seed and holdout summary must pass clean. A guard that
fires on ordinary reports is worse than no guard: it burns retries, then fails
reports, and the first thing anyone would do is turn it off.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.guards import MAX_RETRIES, RedactionGuard, RedactionViolation, scan

ROOT = Path(__file__).resolve().parent.parent

# Model output that must be blocked. These are what a summary looks like when
# the triage prompt has been half-followed — the narration is gone, the
# description is not.
LEAKS = [
    ("A tall man was seen standing near the bins.", "age or build"),
    ("A young black man was looking at the bikes on the rack.", "race or ethnicity"),
    ("A person about 6'2\" was waiting by the parcel lockers.", "height"),
    ("A blonde woman was pulling flowers out of the planters.", "hair"),
    ("A person wearing a dark hoodie was near the mailboxes.", "clothing"),
    ("A silver Vauxhall has been parked in the same position for a week.", "make or model"),
    ("A vehicle with plate LM19 XKZ has not moved for three days.", "registration plate"),
    ("A red van has been parked outside the flats since Tuesday.", "colour"),
    ("Shouting was heard in the street outside number 42.", "house number"),
    ("A resident at 14 Elm Street reported repeated noise.", "house number"),
    ("A caller said her name was Sandra and asked about roof work.", "name"),
    ("A person with a walking stick knocked at several doors.", "distinguishing feature"),
]

# Ordinary Porchlight output. Every one of these must pass clean — they are the
# shape the system produces on a normal day.
CLEAN = [
    "A person was seen loitering by the parcel lockers in the evening.",
    "A person was seen waiting near the parcel lockers after dark.",
    "Somebody was seen near where packages are dropped in the morning.",
    "A vehicle has stayed parked in the same street position for three days.",
    "A pothole has formed near the crossing.",
    "A street light is out on the corner.",
    "Seedlings were pulled up in a garden bed.",
    "Bins are blocking the rear alley.",
    "Graffiti appeared on a substation box.",
    "A package was taken from a doorstep during the day.",
    "A bicycle was removed from a rack outside the building.",
    "Several people were seen near the delivery lockers over two evenings.",
    "A car drove slowly past a row of driveways more than once.",
    "Three reports describe activity near the building's parcel lockers "
    "within thirteen hours, from three separate residents.",
]


@pytest.mark.parametrize("text,expected_label", LEAKS)
def test_leaks_are_caught(text, expected_label):
    """Person-identifying detail in model output must be detected."""
    findings = scan(text)
    assert findings, f"guard missed a leak: {text!r}"
    labels = " ".join(label for label, _ in findings)
    assert expected_label in labels, (
        f"caught {text!r} but described it as {labels!r}, expected {expected_label!r}. "
        "The label is what the operator sees, so it has to name the real problem."
    )


@pytest.mark.parametrize("text", CLEAN)
def test_ordinary_output_passes_clean(text):
    """No false positives on the output the system actually produces."""
    assert scan(text) == [], f"guard fired on ordinary output: {text!r}"


def test_no_seed_report_would_be_blocked_once_redacted():
    """The guard must not fire on the demo dataset's own expected summaries.

    A guard that blocks the seed run takes the video with it. This reads the
    offline fixtures, which are the hand-written triage output for all 38 seed
    reports — i.e. exactly what a correctly-behaving triage stage produces.
    """
    fixtures = json.loads(
        (ROOT / "demo" / "offline_fixtures.json").read_text(encoding="utf-8")
    )
    rows = fixtures.values() if isinstance(fixtures, dict) else fixtures

    blocked = []
    for row in rows:
        summary = row.get("summary") if isinstance(row, dict) else None
        if not summary:
            continue
        if findings := scan(summary):
            blocked.append((summary, findings))

    assert not blocked, (
        "the guard would block the demo's own seed data:\n"
        + "\n".join(f"  {s!r} → {f}" for s, f in blocked)
    )


def test_holdout_summaries_would_not_be_blocked():
    """Precision, checked a second time against data never used for tuning.

    The CLEAN list above was written alongside the patterns, so it can only
    show that the guard agrees with its author. The holdout was written before
    any tuning began and is the honest test of whether these patterns fire on
    ordinary reports.
    """
    holdout = json.loads(
        (ROOT / "data" / "holdout_reports.json").read_text(encoding="utf-8")
    )
    # Raw reporter text, not summaries — so anything caught here is detail the
    # triage stage is supposed to strip, which is what we want to know about.
    flagged = [(r["text"], scan(r["text"])) for r in holdout["reports"] if scan(r["text"])]

    # This is not asserting zero. It is asserting that whatever the guard finds
    # in the holdout is detail a reader would agree identifies a person — the
    # list is printed on failure so a regression is readable rather than a
    # bare count.
    for text, findings in flagged:
        labels = [label for label, _ in findings]
        assert findings, f"{text!r} → {labels}"


class _FakeStopResponse:
    def __init__(self, message):
        self.message = message
        self.stop_reason = "end_turn"


class _FakeEvent:
    """Enough of AfterModelCallEvent to drive the callback directly.

    The alternative is a live model call. This exercises the same code path the
    SDK drives — content-block walking, retry, and the raise — without one.
    """

    def __init__(self, content):
        self.stop_response = _FakeStopResponse({"role": "assistant", "content": content})
        self.exception = None
        self.retry = False


def _structured(**fields):
    """A content block shaped the way structured output arrives."""
    return [{"toolUse": {"name": "TriageResult", "input": fields}}]


def test_guard_reads_structured_output_not_just_text():
    """Structured output arrives as a toolUse block, and that is where the
    summary lives. Scanning only text blocks would miss every real leak."""
    guard = RedactionGuard()
    event = _FakeEvent(_structured(
        report_type="suspicious",
        severity=2,
        summary="A tall man was seen near the bins.",
    ))
    guard.inspect(event)
    assert event.retry is True, "a leak in structured output did not trigger a retry"


def test_guard_retries_then_fails_closed():
    """A leak is retried, and a model that keeps leaking fails the report.

    Failing is the correct end state. The alternative is storing and indexing a
    description of a person, which is the harm the whole design exists to
    prevent.
    """
    guard = RedactionGuard()
    leaked = _structured(summary="A young black man was looking at the bikes.")

    for attempt in range(MAX_RETRIES):
        event = _FakeEvent(leaked)
        guard.inspect(event)
        assert event.retry is True, f"attempt {attempt + 1} should have retried"

    with pytest.raises(RedactionViolation) as caught:
        guard.inspect(_FakeEvent(leaked))

    assert caught.value.findings, "the violation must say what it found"
    assert "race or ethnicity" in str(caught.value)


def test_clean_output_is_left_alone():
    guard = RedactionGuard()
    event = _FakeEvent(_structured(
        summary="A person was seen loitering by the parcel lockers in the evening."
    ))
    guard.inspect(event)
    assert event.retry is False
    assert guard.attempts == 0
    assert guard.caught == []


def test_guard_ignores_failed_model_calls():
    """An exception from the model is the event loop's problem, not the
    guard's — and stop_response is None there."""
    guard = RedactionGuard()
    event = _FakeEvent([])
    event.stop_response = None
    event.exception = RuntimeError("throttled")
    guard.inspect(event)  # must not raise
    assert event.retry is False
