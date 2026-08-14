"""The anomaly detector must judge a zone against itself, not against others.

This is the whole reason the module exists rather than a threshold on a raw
count. Four reports in two days is unremarkable on a busy through-road and a
genuine change in a quiet courtyard, and a detector that cannot tell those
apart would fire on the busiest streets forever.

Pure maths — no database, no agent, no network.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from src.tools.anomaly import measure

TZ = timezone(timedelta(hours=-5))
NOW = datetime(2026, 4, 8, 12, 0, tzinfo=TZ)


def history(rate_per_day: float, days: int, end: datetime) -> list[datetime]:
    """Evenly spaced timestamps at a given rate, ending before `end`."""
    total = int(rate_per_day * days)
    if total == 0:
        return []
    step = timedelta(days=days) / total
    return [end - timedelta(days=days) + step * i for i in range(total)]


def burst(count: int, end: datetime, hours: float = 36.0) -> list[datetime]:
    """`count` reports spread across the last `hours` before `end`."""
    if count == 1:
        return [end]
    step = timedelta(hours=hours) / (count - 1)
    return [end - timedelta(hours=hours) + step * i for i in range(count)]


def test_quiet_zone_spike_is_flagged():
    """Four reports in 36h where the zone normally sees two a week."""
    window_start = NOW - timedelta(hours=48)
    past = history(rate_per_day=2 / 7, days=35, end=window_start)
    recent = burst(4, NOW)

    d = measure("Parcel lockers, bldg 3", past + recent, NOW)

    assert d.observed_count == 4
    assert d.baseline_count == len(past)
    assert d.z_score > 3.0, f"quiet-zone spike scored only z={d.z_score}"
    assert d.tail_probability < 0.01


def test_busy_zone_same_burst_is_ordinary():
    """The identical burst in a zone that normally sees three a day."""
    window_start = NOW - timedelta(hours=48)
    past = history(rate_per_day=3.0, days=35, end=window_start)
    recent = burst(4, NOW)

    d = measure("Elm St north", past + recent, NOW)

    assert d.observed_count == 4
    assert d.z_score < 1.0, f"busy zone flagged an ordinary week: z={d.z_score}"
    assert d.tail_probability > 0.5


def test_same_count_scores_differently_by_zone():
    """The point of the module, stated as one assertion."""
    window_start = NOW - timedelta(hours=48)
    recent = burst(4, NOW)

    quiet = measure("quiet", history(2 / 7, 35, window_start) + recent, NOW)
    busy = measure("busy", history(3.0, 35, window_start) + recent, NOW)

    assert quiet.observed_count == busy.observed_count
    assert quiet.z_score > busy.z_score * 3, (
        f"identical counts scored too similarly: quiet z={quiet.z_score}, "
        f"busy z={busy.z_score}"
    )


def test_zone_with_no_history_does_not_divide_by_zero():
    """A first-ever report must not produce inf, nan, or an exception.

    Textbook z-scores divide by a sample standard deviation, which is zero for
    a zone with no history or a flat one — exactly the quiet zones this product
    cares most about.
    """
    d = measure("Brand new zone", burst(1, NOW), NOW)

    assert d.baseline_count == 0
    assert d.observed_count == 1
    assert d.z_score == d.z_score  # not nan
    assert abs(d.z_score) < 100  # not inf


def test_flat_history_does_not_divide_by_zero():
    """A zone with a perfectly constant rate has zero sample variance."""
    window_start = NOW - timedelta(hours=48)
    past = history(rate_per_day=1.0, days=30, end=window_start)

    d = measure("Steady zone", past + burst(1, NOW), NOW)

    assert d.z_score == d.z_score
    assert abs(d.z_score) < 100


def test_counts_are_returned_with_the_score():
    """The agent is asked to reason about the number, so it gets the workings."""
    window_start = NOW - timedelta(hours=48)
    past = history(0.5, 20, window_start)
    d = measure("Willow Ct", past + burst(2, NOW), NOW).as_dict()

    for key in (
        "observed_count",
        "baseline_count",
        "baseline_days",
        "baseline_rate_per_window",
        "z_score",
        "tail_probability",
    ):
        assert key in d, f"{key} missing — the agent cannot weigh a bare score"
