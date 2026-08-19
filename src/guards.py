"""Structural enforcement of the §4.1 redaction guarantee.

The triage prompt tells the model to strip person-identifying detail, and
``tests/test_redaction.py`` checks that it does. Both are necessary and neither
is a control: a prompt is an instruction a model may not follow, and a test
tells you about the twelve cases you thought of, after the fact, on your
machine.

This module is the control. It runs inside the agent loop, sees what the model
actually produced, and refuses to let it out.

    prompt   →  asks the model to redact          (primary, does the work)
    guard    →  refuses output that didn't        (backstop, this file)
    tests    →  prove both hold on real cases     (evidence)

**Why a hook rather than a check in the pipeline.** A pipeline check can only
reject a finished result, which means the report is lost or the run dies.
Strands' ``AfterModelCallEvent`` carries a ``retry`` flag: setting it discards
the model's response and re-invokes it, before anything downstream sees the
output. So a leak becomes a retry rather than a failure, and the retry costs one
Haiku call. Only if the model leaks repeatedly does this fail the report — which
is the correct end state for a safety control, and is loud rather than silent.

**Precision over recall, deliberately.** A false positive here costs real money
and can abort a demo run, so the patterns match constructions that are
unambiguously person-identifying and leave the borderline ones to the prompt.
This is a net under the prompt, not a replacement for it. Recall is what
``tests/test_redaction.py`` measures, against a live model.
"""

from __future__ import annotations

import os
import re
from typing import Any, Iterable

from strands.hooks import AfterModelCallEvent, HookProvider, HookRegistry

# How many times to let the model try again before giving up on the report.
# Two is enough for a model that leaked by accident and not enough to burn
# money on one that is going to keep doing it.
MAX_RETRIES = int(os.environ.get("FNA_GUARD_RETRIES", "2"))

_PERSON = r"(?:m[ae]n|wom[ae]n|guy|guys|lad|lads|male|female|boy|girl|teen|teenager|youth|person|people|kid|kids)"
_VEHICLE = r"(?:car|van|truck|lorry|suv|sedan|hatchback|motorbike|scooter|bike|vehicle)"
_COLOUR = r"(?:black|white|silver|grey|gray|red|blue|green|yellow|brown|beige)"
_STREET = r"(?:street|st|road|rd|avenue|ave|lane|ln|drive|dr|close|court|ct|way|terrace)"

# Each pattern is (label, regex). The label is what the error reports, so it
# has to name the thing a person would need to fix.
PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "a person described by race or ethnicity",
        re.compile(
            rf"\b(?:black|white|asian|hispanic|latino|latina|arab|middle[\s-]?eastern|"
            rf"african|caribbean|eastern[\s-]?european)\s+{_PERSON}\b",
            re.I,
        ),
    ),
    (
        "a person described by age or build",
        re.compile(
            rf"\b(?:young|old|older|elderly|middle[\s-]?aged|teenage|tall|short|"
            rf"heavy[\s-]?set|slim|thin|stocky|skinny|fat|large|small)\s+{_PERSON}\b",
            re.I,
        ),
    ),
    (
        "a person described by hair or a distinguishing feature",
        re.compile(
            rf"\b(?:blonde|blond|brunette|ginger|red[\s-]?haired|dark[\s-]?haired|"
            rf"grey[\s-]?haired|bald|bearded|tattooed|glasses|dreadlocks)\b"
            rf"(?:\s+\w+){{0,2}}\s+{_PERSON}\b|"
            rf"\b{_PERSON}\s+with\s+(?:\w+\s+){{0,2}}"
            rf"(?:hair|beard|tattoo|tattoos|glasses|dreadlocks|walking\s+stick)\b",
            re.I,
        ),
    ),
    (
        "a height",
        re.compile(r"\b\d\s?(?:'|ft|feet|foot)\s?\d{0,2}\s?(?:\"|in|inches)?\b", re.I),
    ),
    (
        "clothing worn by a person",
        re.compile(
            # Up to two adjectives between the article and the garment, so
            # "a dark hoodie" and "a bright red cap" are both caught without
            # having to enumerate every colour word a reporter might reach for.
            r"\b(?:wearing|dressed\s+in|in)\s+an?\s+(?:\w+[\s-]){0,2}"
            r"(?:hoodie|hood|jacket|coat|cap|hat|beanie|mask|balaclava|"
            r"tracksuit|shirt|jumper|scarf|uniform|overalls)\b",
            re.I,
        ),
    ),
    (
        "a vehicle registration plate",
        re.compile(
            r"\b(?:[A-Z]{2}\d{2}\s?[A-Z]{3}|[A-Z]\d{3}\s?[A-Z]{3}|"
            r"\d[A-Z]{3}\d{3}|[A-Z]{3}[\s-]?\d{3,4})\b"
        ),
    ),
    (
        "a vehicle make or model",
        re.compile(
            r"\b(?:vauxhall|ford|vw|volkswagen|bmw|audi|mercedes|toyota|honda|nissan|"
            r"peugeot|renault|citroen|skoda|seat|kia|hyundai|volvo|tesla|jeep|"
            r"chevrolet|chevy|dodge|subaru|mazda|lexus|transit|astra|corsa|golf|"
            r"civic|focus|fiesta)\b",
            re.I,
        ),
    ),
    (
        "a vehicle identified by colour",
        re.compile(rf"\b{_COLOUR}\s+{_VEHICLE}\b", re.I),
    ),
    (
        "a house number",
        re.compile(
            rf"\b(?:(?:at|from|outside|near|opposite)\s+)?"
            rf"(?:number|no\.?|#)\s?\d{{1,4}}\b|"
            rf"\b\d{{1,4}}\s+[A-Z][a-z]+\s+{_STREET}\b",
            re.I,
        ),
    ),
    (
        "a person's name",
        re.compile(
            r"\b(?:name\s+(?:is|was)|named|called|goes\s+by)\s+[A-Z][a-z]{2,}\b|"
            r"\b(?:mr|mrs|ms|miss|dr)\.?\s+[A-Z][a-z]{2,}\b"
        ),
    ),
]


class RedactionViolation(RuntimeError):
    """Person-identifying detail survived redaction and could not be cleared.

    Raised only after the model has been given ``MAX_RETRIES`` further attempts.
    Failing the report is the correct outcome: the alternative is storing and
    indexing a description of a person, which is the harm this whole design
    exists to prevent.
    """

    def __init__(self, findings: list[tuple[str, str]], attempts: int):
        self.findings = findings
        self.attempts = attempts
        detail = "; ".join(f"{label} ({match!r})" for label, match in findings)
        super().__init__(
            f"redaction guard blocked model output after {attempts} attempts: {detail}"
        )


def scan(text: str) -> list[tuple[str, str]]:
    """Find person-identifying detail in a piece of model output.

    Returns a list of ``(what it is, the text that matched)``. Empty means
    clean. Pure and side-effect free, so the patterns can be tested without a
    model, an agent, or an AWS account — see ``tests/test_guards.py``.
    """
    findings: list[tuple[str, str]] = []
    for label, pattern in PATTERNS:
        match = pattern.search(text)
        if match:
            findings.append((label, match.group(0).strip()))
    return findings


def _texts(content: Iterable[dict[str, Any]]) -> list[str]:
    """Pull every string a content block carries.

    Structured output arrives as a ``toolUse`` block whose ``input`` holds the
    generated fields, so scanning only ``text`` blocks would miss the summary
    and the alert message — which are the two fields that matter. This walks
    both.
    """
    out: list[str] = []

    def walk(value: Any) -> None:
        if isinstance(value, str):
            out.append(value)
        elif isinstance(value, dict):
            for v in value.values():
                walk(v)
        elif isinstance(value, (list, tuple)):
            for v in value:
                walk(v)

    for block in content or []:
        if "text" in block:
            walk(block["text"])
        if "toolUse" in block:
            walk(block["toolUse"].get("input"))
    return out


class RedactionGuard(HookProvider):
    """Blocks model output that still identifies a person, and asks again.

    Attach to any agent whose output is stored, indexed, or shown to a person:

        Agent(..., hooks=[RedactionGuard()])

    One instance per agent invocation — the retry counter is per-report, and
    the agents are constructed per report, so this falls out naturally.
    """

    def __init__(self, label: str = "agent", max_retries: int = MAX_RETRIES):
        self.label = label
        self.max_retries = max_retries
        self.attempts = 0
        # Kept for the demo and for tests: what was caught and retried, rather
        # than only what finally failed. A guard that never reports its near
        # misses gives you no way to tell whether it is doing anything.
        self.caught: list[tuple[str, str]] = []

    def register_hooks(self, registry: HookRegistry, **kwargs: Any) -> None:
        registry.add_callback(AfterModelCallEvent, self.inspect)

    def inspect(self, event: AfterModelCallEvent) -> None:
        if event.exception is not None or event.stop_response is None:
            return

        message = event.stop_response.message or {}
        findings: list[tuple[str, str]] = []
        for text in _texts(message.get("content", [])):
            findings.extend(scan(text))

        if not findings:
            return

        self.caught.extend(findings)

        if self.attempts >= self.max_retries:
            raise RedactionViolation(findings, self.attempts + 1)

        # Discard this response and make the model produce another one. The
        # leaked version never reaches the pipeline, never reaches storage, and
        # never reaches the index.
        self.attempts += 1
        event.retry = True
