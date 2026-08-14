"""Pipeline wiring, offline.

Only the three model calls are stubbed. Storage, the vector index, the anomaly
detector, the evidence computation, alert suppression, and the renderer all run
for real, so this covers everything except the judgment itself — and it runs in
CI with no AWS credentials and no spend.

What it is protecting:

* ``build_summary`` counts reporters, zones, and time spans from storage rather
  than trusting the correlation agent. That is the §4.2 safety control.
* A cluster that has already alerted must not alert again.
* A stage failure must name the stage.

The full 38-report seed run against real models is verification step 5 and is
run by hand — see IMPLEMENTATION_PLAN.md §7.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from src import pipeline, render
from src.models import (
    CorrelationResult,
    EscalationDecision,
    RawReport,
    TriageResult,
)
from src.tools import storage, vectors

TZ = timezone(timedelta(hours=-5))
T0 = datetime(2026, 4, 6, 9, 0, tzinfo=TZ)

# Already written the way triage would write them, so the stub is a pass-through
# and the retrieval being exercised is the real thing.
#   (offset_hours, zone, reporter, summary)
CLUSTER = [
    (0, "Parcel lockers, bldg 3", "r001", "A person was seen loitering by the parcel lockers in the evening."),
    (3, "Parcel lockers, bldg 3", "r002", "A person was seen waiting near the parcel lockers after dark."),
    (20, "Parcel lockers, bldg 3", "r003", "A person was seen standing by the parcel lockers in the morning."),
    (30, "Parcel lockers, bldg 3", "r004", "A person was seen near the building's parcel lockers again."),
]
SINGLE_REPORTER = [
    (5, "Maple & 3rd", "r009", "A vehicle has stayed parked in the same street position for three days."),
    (29, "Maple & 3rd", "r009", "The same vehicle remains parked and has not moved."),
    (53, "Maple & 3rd", "r009", "The vehicle is still parked in the same position and has not moved all week."),
]
NOISE = [
    (1, "Elm St north", "r010", "A pothole has formed near the crossing."),
    (7, "Birch Ln", "r011", "A street light is out on the corner."),
    (12, "Community garden", "r012", "Seedlings were pulled up in a garden bed."),
    (18, "Rear alley, bldg 1", "r013", "Bins are blocking the alley."),
    (26, "Elm St south", "r014", "Graffiti appeared on a substation box."),
]

ALL = sorted(CLUSTER + SINGLE_REPORTER + NOISE, key=lambda r: r[0])


@pytest.fixture()
def wired(tmp_path, monkeypatch):
    """Real everything except the three model calls."""
    monkeypatch.setenv("FNA_DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("FNA_CHROMA_PATH", str(tmp_path / "chroma"))
    monkeypatch.setenv("FNA_ALERT_LOG", str(tmp_path / "alerts.log"))
    monkeypatch.setattr(storage, "DB_PATH", tmp_path / "test.db")

    vectors.reset()
    storage.init_db()

    def fake_triage(raw: RawReport) -> TriageResult:
        return TriageResult(report_type="suspicious", severity=2, summary=raw.text)

    def fake_correlate(report) -> CorrelationResult:
        # Real semantic search — this is the part worth exercising.
        hits = vectors.search(
            report.summary, limit=8, exclude_ids=[report.report_id]
        )
        related = [h["report_id"] for h in hits if h["similarity"] >= 0.55]
        return CorrelationResult(
            related_report_ids=related,
            assessment=f"{len(related)} similar report(s) found.",
        )

    def fake_decide(report, summary) -> EscalationDecision:
        # Deliberately mirrors the shape of the real judgment so suppression
        # and evidence handling are exercised, without pretending to be it.
        alert = (
            summary.cluster_size >= 3
            and summary.distinct_reporters >= 3
            and summary.time_span_hours <= 48
            and len(summary.zones_involved) == 1
        )
        return EscalationDecision(
            action="alert" if alert else "silent_log",
            urgency="medium",
            audience="block_captain",
            message="Worth a look at the parcel lockers this week." if alert else "",
            reasoning=(
                f"{summary.cluster_size} reports from {summary.distinct_reporters} "
                f"reporters over {summary.time_span_hours:.0f}h."
            ),
        )

    monkeypatch.setattr(pipeline, "triage", fake_triage)
    monkeypatch.setattr(pipeline, "correlate", fake_correlate)
    monkeypatch.setattr(pipeline, "decide", fake_decide)

    yield tmp_path
    vectors.reset()


def run_all(rows=ALL) -> list[pipeline.Processed]:
    out = []
    for offset, zone, reporter, summary in rows:
        out.append(
            pipeline.process_report(
                RawReport(
                    text=summary,
                    zone=zone,
                    reporter_id=reporter,
                    timestamp=T0 + timedelta(hours=offset),
                )
            )
        )
    return out


def test_exactly_one_alert_and_it_is_the_real_cluster(wired):
    """The behaviour that actually matters, asserted the way it matters.

    Not "the alert fires on report 4" — by report 3 there are already three
    distinct reporters in one zone inside a day, which is a defensible place to
    fire. What must hold is that exactly one alert leaves the system and it
    belongs to the genuine cluster.
    """
    results = run_all()
    alerts_sent = [r for r in results if r.outcome == "alert"]

    assert len(alerts_sent) == 1, (
        f"expected exactly one alert, got {len(alerts_sent)}: "
        f"{[r.report.zone for r in alerts_sent]}"
    )
    assert alerts_sent[0].report.zone == "Parcel lockers, bldg 3"


def test_repeat_alerts_are_suppressed(wired):
    """A later report joining an alerted cluster is logged, not re-alerted.

    Without this the demo shows two alerts instead of one, and a deployment
    teaches its recipients to ignore it.
    """
    results = run_all()
    locker_results = [r for r in results if r.report.zone == "Parcel lockers, bldg 3"]

    wanted_alert = [r for r in locker_results if r.decision.action == "alert"]
    actually_sent = [r for r in locker_results if r.sent]

    assert len(wanted_alert) > 1, "suppression is untested if only one report ever alerts"
    assert len(actually_sent) == 1
    assert any(r.suppressed for r in locker_results)


def test_single_reporter_run_never_alerts(wired):
    """The §4.2 safety control, end to end.

    Three semantically identical reports, one zone, inside 48 hours — every
    signal a cluster has except corroboration. It must not escalate.
    """
    results = run_all()
    maple = [r for r in results if r.report.zone == "Maple & 3rd"]

    assert maple, "fixture did not produce the single-reporter group"
    assert all(r.outcome != "alert" for r in maple)

    correlated = [r for r in maple if r.summary.cluster_size > 1]
    assert correlated, "the single-reporter reports did not correlate at all"
    assert all(r.summary.distinct_reporters == 1 for r in correlated)


def test_counts_come_from_storage_not_the_agent(wired):
    """distinct_reporters is a safety control, so it is counted, not reported.

    The stub correlation agent returns ids and nothing else. Every figure the
    escalation stage weighs has to have been derived here.
    """
    results = run_all()
    biggest = max(results, key=lambda r: r.summary.cluster_size)
    s = biggest.summary

    cluster_ids = [biggest.report.report_id, *s.related_report_ids]
    stored = storage.get_reports(cluster_ids)

    assert s.cluster_size == len(stored)
    assert s.distinct_reporters == len({r.reporter_id for r in stored})
    assert s.zones_involved == sorted({r.zone for r in stored})


def test_noise_is_logged_silently(wired):
    """The common case, and the one the product is about."""
    results = run_all()
    noise_zones = {row[1] for row in NOISE}
    noise = [r for r in results if r.report.zone in noise_zones]

    assert len(noise) == len(NOISE)
    assert all(r.outcome == "silent" for r in noise)


def test_stage_failure_names_the_stage(wired, monkeypatch):
    """Three models and four tools deep, 'it broke' is not a usable error."""
    def boom(_raw):
        raise ValueError("model unavailable")

    monkeypatch.setattr(pipeline, "triage", boom)

    with pytest.raises(pipeline.StageError) as exc:
        run_all(rows=NOISE[:1])

    assert exc.value.stage == "triage"
    assert "model unavailable" in str(exc.value)


def test_render_matches_the_run(wired, tmp_path):
    """Verification step 6: the picture must agree with the log.

    Both read the same SQLite rows. A graph that contradicts the terminal is
    worse than no graph.
    """
    results = run_all()
    rows = storage.rendered_rows()

    assert len(rows) == len(ALL)
    assert sum(r["action"] == "alert" for r in rows) == sum(
        r.outcome == "alert" for r in results
    )

    out = render.write(tmp_path / "report.html")
    page = out.read_text(encoding="utf-8")

    assert page.startswith("<!doctype html>")
    assert "<svg" in page and "</svg>" in page
    assert "http://" not in page and "https://" not in page, "page is not self-contained"
    assert page.count("<circle") >= len(ALL), "not every report got a node"


def test_suppressed_report_is_covered_by_the_alert(wired):
    """A suppressed duplicate must be recorded as part of the situation.

    Both bugs this guards against were invisible in the test suite and obvious
    the moment the page was looked at. Without coverage extending to the
    suppressed report:

    * the graph drew a four-report cluster as three, because only nodes marked
      covered are lit; and
    * the suppressed duplicate passed the "genuine decline" filter and took the
      card slot meant for the near-miss, so the page restated the alert instead
      of showing the decline the product exists to demonstrate.
    """
    results = run_all()
    locker = [r for r in results if r.report.zone == "Parcel lockers, bldg 3"]
    assert any(r.suppressed for r in locker), "fixture stopped exercising suppression"

    rows = {r["report_id"]: r for r in storage.rendered_rows()}
    for res in locker:
        assert rows[res.report.report_id]["covered"], (
            f"{res.report.report_id} is part of the alerted cluster but is not "
            "marked covered — it will be drawn dim and can masquerade as a "
            "genuine decline"
        )

    # And nothing an alert covers is offered as a genuine decline.
    genuine = [r for r in rows.values() if r["cluster_size"] > 1
               and r["action"] != "alert" and not r["covered"]]
    assert all(r["zone"] != "Parcel lockers, bldg 3" for r in genuine)


def test_no_two_nodes_overlap(wired):
    """Every report must be individually visible in the graph.

    Caught by eye, not by the suite: cluster members were placed at random
    angles around their centroid with no separation check, so two of the four
    escalated nodes landed 3px apart. The page showed a four-report cluster as
    two blobs with edges running between them, which is worse than showing
    nothing — it silently understates the evidence the alert was based on.
    """
    import itertools
    import math
    import re

    run_all()
    html = render.build_html(storage.rendered_rows())

    circles = re.findall(
        r"<circle cx='([\d.]+)' cy='([\d.]+)' r='([\d.]+)' fill='(#\w+)'", html
    )
    nodes = [(float(x), float(y), float(r)) for x, y, r, _ in circles]
    assert len(nodes) == len(ALL), "not every report got a node"

    for (x1, y1, r1), (x2, y2, r2) in itertools.combinations(nodes, 2):
        gap = math.dist((x1, y1), (x2, y2))
        assert gap >= r1 + r2, (
            f"two nodes overlap: centres {gap:.1f}px apart but radii sum to "
            f"{r1 + r2:.1f}. Reports are being hidden behind each other."
        )


def test_layout_is_deterministic(wired, tmp_path):
    """Same data must draw the same picture, so a take can be re-shot."""
    run_all()
    first = render.build_html(storage.rendered_rows())
    second = render.build_html(storage.rendered_rows())
    assert first == second
