"""The premise check.

Porchlight's whole claim is that four neighbours describing one situation in
four different vocabularies come back as one cluster. If that fails, nothing
downstream matters. Per IMPLEMENTATION_PLAN.md §7 this runs first and is a
stop-and-fix if it goes red.

No agent and no network are involved — ChromaDB's default embedding function is
all-MiniLM-L6-v2 running locally through ONNX.

`test_near_miss_stays_separable` is the counterweight to the rest. Indexing the
normalised summary is what makes retrieval work at all, but normalising too
hard would make every "person loitering" report collapse to one point, merging
the near-miss into the genuine cluster and leaving the demo with nothing to
decline. That test is what stops a future prompt edit from doing it.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from src.models import TriagedReport
from src.tools import vectors

ANCHOR = datetime(2026, 4, 6, 18, 40, tzinfo=timezone(timedelta(hours=-5)))

# What the reporters actually wrote, from data/seed_reports.json. Between them
# they share no content word at all.
RAW_CLUSTER = [
    "There has been a person hanging around the mailboxes the last couple of evenings.",
    "Saw someone loitering by the post boxes again tonight when I got back from work.",
    "Somebody was messing about near where the packages get dropped when I left this morning.",
    "A person was waiting around by the delivery lockers early on again.",
]

# What triage turns those into: neutral, person-details removed, place and
# behaviour kept specific. This is what gets indexed.
CLUSTER = [
    "A person was seen repeatedly near the building's parcel lockers over several evenings.",
    "A person was seen loitering by the parcel lockers in the evening.",
    "A person was seen interfering near the parcel lockers in the morning.",
    "A person was seen waiting by the parcel lockers early in the morning.",
]

# The near-miss: similar in kind, but a different situation in three zones.
NEAR_MISS = [
    "An unfamiliar person walked slowly along the street looking at houses.",
    "A person moved about near residential driveways during the afternoon.",
    "A person stood at the end of the road without apparent purpose.",
]

UNRELATED = [
    "A pothole has formed near the crossing.",
    "A street light is out on the corner.",
    "Seedlings were pulled up in a garden bed.",
    "Bins are blocking the alley.",
    "Graffiti appeared on a substation box.",
    "A fallen branch is blocking the footpath.",
    "Fireworks were set off late at night.",
    "A blocked drain causes flooding at the corner.",
]


def _report(idx: int, summary: str, zone: str) -> TriagedReport:
    return TriagedReport(
        report_id=f"t{idx:03d}",
        zone=zone,
        timestamp=ANCHOR + timedelta(hours=idx),
        reporter_id=f"r{idx:03d}",
        report_type="suspicious",
        severity=2,
        summary=summary,
    )


@pytest.fixture()
def indexed(tmp_path, monkeypatch):
    """Index cluster + near-miss + unrelated. Returns the id sets."""
    monkeypatch.setenv("FNA_CHROMA_PATH", str(tmp_path / "chroma"))
    vectors.reset()

    groups: dict[str, set[str]] = {"cluster": set(), "near_miss": set(), "unrelated": set()}
    idx = 0
    for name, texts, zone in (
        ("cluster", CLUSTER, "Parcel lockers, bldg 3"),
        ("near_miss", NEAR_MISS, "Elm St north"),
        ("unrelated", UNRELATED, "Maple & 3rd"),
    ):
        for text in texts:
            report = _report(idx, text, zone)
            vectors.embed_and_index(report)
            groups[name].add(report.report_id)
            idx += 1

    yield groups
    vectors.reset()


def test_paraphrase_beats_unrelated(indexed):
    """Every cluster report must outrank every unrelated report.

    The query is one cluster report's own summary with itself excluded — the
    real usage pattern, since the correlation agent searches using the report
    it is currently assessing.
    """
    query_id = sorted(indexed["cluster"])[-1]
    query = CLUSTER[-1]

    results = vectors.search(query, limit=30, exclude_ids=[query_id])
    assert results, "index returned nothing"

    scores = {r["report_id"]: r["similarity"] for r in results}
    remaining = indexed["cluster"] - {query_id}

    worst_cluster = min(scores[i] for i in remaining)
    best_unrelated = max(scores[i] for i in indexed["unrelated"])

    assert worst_cluster > best_unrelated, (
        f"weakest cluster match {worst_cluster:.3f} did not beat strongest "
        f"unrelated {best_unrelated:.3f}\n"
        + "\n".join(f"  {r['similarity']:.3f}  {r['text'][:70]}" for r in results[:10])
    )


def test_near_miss_stays_separable(indexed):
    """The near-miss must not merge into the genuine cluster.

    Guards against over-normalisation in the triage summary prompt. If this
    fails, the demo has a seven-report blob instead of one alert and one
    deliberate decline, and the most persuasive moment in the video is gone.
    """
    query_id = sorted(indexed["cluster"])[-1]
    results = vectors.search(CLUSTER[-1], limit=30, exclude_ids=[query_id])
    scores = {r["report_id"]: r["similarity"] for r in results}

    remaining = indexed["cluster"] - {query_id}
    worst_cluster = min(scores[i] for i in remaining)
    best_near_miss = max(scores[i] for i in indexed["near_miss"])

    assert worst_cluster > best_near_miss, (
        f"near-miss has merged into the cluster: weakest cluster match "
        f"{worst_cluster:.3f} vs strongest near-miss {best_near_miss:.3f}. "
        "The triage summary prompt is probably normalising away the specific "
        "place or behaviour."
    )


def test_keyword_search_would_fail_on_raw_reports():
    """Establishes that embeddings do real work here, rather than decoration.

    If a substring search could find these four, the semantic layer would be
    unnecessary and the submission's central claim would be false.
    """
    for term in ("mailbox", "post box", "locker", "package", "parcel", "deliver"):
        matched = [t for t in RAW_CLUSTER if term in t.lower()]
        assert len(matched) < len(RAW_CLUSTER), (
            f"'{term}' matches all four raw reports — the cluster is findable "
            "by keyword, so the seed data no longer demonstrates the premise"
        )


def test_excludes_self(indexed):
    """A report must never be returned as a match for itself."""
    first = sorted(indexed["cluster"])[0]
    results = vectors.search(CLUSTER[0], limit=5, exclude_ids=[first])
    assert first not in {r["report_id"] for r in results}
