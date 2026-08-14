"""Per-zone anomaly detection.

A zone is compared against **its own history**, never against other zones. A
busy street with six reports a week is not an anomaly; a quiet courtyard with
four reports in two days is. That distinction is the whole reason this module
exists rather than a threshold on a raw count.

Counts of arrivals are Poisson-ish, so the baseline rate is estimated from the
zone's own history and the deviation is measured in units of sqrt(rate) rather
than a sample standard deviation. That matters practically: a zone whose
history is a flat run of identical counts has zero sample variance, and a
z-score computed the textbook way divides by zero on exactly the quiet zones
this product cares most about.

The pure functions here take timestamps and return numbers. The ``@tool``
wrapper at the bottom is thin on purpose, so the maths can be tested without
the agent framework in the loop.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta

from scipy import stats
from strands import tool

DEFAULT_WINDOW_HOURS = 48.0

# Smoothing constant for the baseline rate. Without it a zone with no prior
# reports has an estimated rate of zero, and every deviation is infinite.
# 0.5 is the Jeffreys prior for a Poisson rate — small enough not to mask a
# real spike, large enough to keep a first-ever report from reading as one.
_SMOOTHING = 0.5


@dataclass(frozen=True)
class Deviation:
    """An anomaly reading, with the counts it was derived from.

    The counts are part of the return value on purpose. The correlation agent
    is asked to reason about whether a number is meaningful, and it cannot do
    that if all it receives is the number.
    """

    zone: str
    window_hours: float
    observed_count: int
    baseline_days: float
    baseline_count: int
    baseline_rate_per_window: float
    z_score: float
    tail_probability: float

    def as_dict(self) -> dict:
        return asdict(self)


def measure(
    zone: str,
    timestamps: list[datetime],
    now: datetime,
    window_hours: float = DEFAULT_WINDOW_HOURS,
) -> Deviation:
    """Score how unusual this zone's recent report rate is for this zone.

    ``timestamps`` is every report ever logged for the zone, in any order.
    ``now`` is the moment being evaluated — normally the timestamp of the
    report being processed, not wall-clock time, so a run over historical data
    scores each report as it would have been scored at the time.

    Returns a z-score in units of sqrt(baseline rate), plus the probability of
    seeing at least this many reports if nothing had changed.
    """
    window = timedelta(hours=window_hours)
    window_start = now - window

    recent = [t for t in timestamps if window_start < t <= now]
    baseline = [t for t in timestamps if t <= window_start]

    observed = len(recent)

    if not baseline:
        # No history to compare against. Report the count and a rate of
        # essentially zero rather than inventing a baseline — the agent is
        # told the baseline is empty and can weigh it accordingly.
        baseline_days = 0.0
        baseline_count = 0
        rate = _SMOOTHING
    else:
        earliest = min(baseline)
        baseline_days = max((window_start - earliest).total_seconds() / 86400.0, window_hours / 24.0)
        baseline_count = len(baseline)
        windows_elapsed = max(baseline_days * 24.0 / window_hours, 1.0)
        rate = (baseline_count + _SMOOTHING) / windows_elapsed

    z = (observed - rate) / math.sqrt(rate)
    tail = float(stats.poisson.sf(observed - 1, rate)) if observed > 0 else 1.0

    return Deviation(
        zone=zone,
        window_hours=window_hours,
        observed_count=observed,
        baseline_days=round(baseline_days, 2),
        baseline_count=baseline_count,
        baseline_rate_per_window=round(rate, 3),
        z_score=round(z, 2),
        tail_probability=float(f"{tail:.4g}"),
    )


@tool
def check_baseline_deviation(zone: str, window_hours: float = DEFAULT_WINDOW_HOURS) -> dict:
    """Check whether a zone's recent report rate is unusual for that zone.

    Compares how many reports this zone received in the last `window_hours`
    against how often that zone normally receives reports. The comparison is
    always against the zone's own history — a busy street and a quiet courtyard
    are held to different baselines, so a count that is ordinary in one is a
    spike in the other.

    Use this when you want to know whether a group of reports represents an
    actual change in a place, rather than that place's normal background level.

    Args:
        zone: The zone label to check, exactly as it appears on a report.
        window_hours: How far back "recent" reaches. Defaults to 48 hours.

    Returns:
        A dict with the reading and the counts behind it:
        - observed_count: reports in the recent window
        - baseline_count / baseline_days: the history it was compared against
        - baseline_rate_per_window: reports this zone normally sees per window
        - z_score: deviation in units of sqrt(rate). Roughly: below 2 is
          ordinary, 2-3 is worth noting, above 3 is a real change in rate.
        - tail_probability: chance of seeing at least this many reports if
          nothing had changed. Small means surprising.

        A zone with no prior history returns baseline_count 0 — treat a high
        score there with more caution, since there is nothing to compare to.
    """
    from src.tools import storage

    timestamps = storage.zone_timestamps(zone)
    now = max(timestamps) if timestamps else datetime.now().astimezone()
    return measure(zone, timestamps, now, window_hours).as_dict()
