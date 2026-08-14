"""Semantic index over reports.

This is the module the project's premise rests on. Four neighbors describing
the same situation as "the mailboxes", "the post boxes", "where the packages
get dropped", and "the delivery lockers" share no keywords at all; if these
four do not come back as one cluster, nothing downstream can save the product.

ChromaDB's default embedding function (all-MiniLM-L6-v2, ONNX, local) is used
deliberately — no API key, no per-embedding cost, no network, and identical
output on every run. Do not pass an embedding function; the default is the one
we want. First use downloads ~80 MB and caches it.

**The triage summary is what gets indexed, never the reporter's raw words.**
That serves two purposes at once, and both were load-bearing:

*Safety* — the summary is the redacted form, so person-identifying detail never
reaches the vector store (IMPLEMENTATION_PLAN.md §4.1).

*Accuracy* — indexing raw text does not work. Measured on the seed cluster, the
weakest cluster report ranked BELOW an unrelated one under every query strategy
tried (separation -0.03 to -0.16); indexing the normalised sentence separates
the same groups by +0.28 to +0.52. Incidental narration ("when I got back from
work", "again tonight") dominates the embedding of a short text. Normalising is
not a compromise for privacy's sake — it is what makes retrieval work.

The tradeoff to watch: normalise too hard and unrelated reports start to look
alike. The summary prompt is explicit about keeping the specific place and
behaviour for exactly this reason, and tests/test_vectors.py asserts the
near-miss group stays separable from the genuine cluster.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from functools import lru_cache

import chromadb
from strands import tool

from src.models import TriagedReport

COLLECTION = "reports"


def chroma_path() -> str:
    # Read at call time, not import time, so tests can point this at a tmp dir
    # without having to control import order.
    return os.environ.get("FNA_CHROMA_PATH", "chroma")


@lru_cache(maxsize=4)
def _collection_for(path: str):
    client = chromadb.PersistentClient(path=path)
    # Pin the distance metric rather than relying on the default, so
    # `similarity = 1 - distance` below is meaningful rather than a guess.
    return client.get_or_create_collection(
        name=COLLECTION, metadata={"hnsw:space": "cosine"}
    )


def _collection():
    return _collection_for(chroma_path())


def embed_and_index(report: TriagedReport) -> None:
    """Add a report to the semantic index. Idempotent on report_id.

    Called directly by the pipeline, never by an agent — a report that silently
    fails to be indexed is invisible to every later search.
    """
    _collection().upsert(
        ids=[report.report_id],
        documents=[report.summary],
        metadatas=[
            {
                "zone": report.zone,
                "timestamp": report.timestamp.isoformat(),
                "epoch": report.timestamp.timestamp(),
                "report_type": report.report_type,
                "severity": report.severity,
            }
        ],
    )


def reset() -> None:
    """Drop the collection. Used by the demo and by tests."""
    client = chromadb.PersistentClient(path=chroma_path())
    try:
        client.delete_collection(COLLECTION)
    except Exception:
        pass
    _collection_for.cache_clear()


def search(
    query: str,
    limit: int = 8,
    zone: str | None = None,
    days: int | None = None,
    exclude_ids: list[str] | None = None,
    now: datetime | None = None,
) -> list[dict]:
    """Similarity search over indexed reports. Pure function; see the tool below."""
    col = _collection()
    if col.count() == 0:
        return []

    where: dict = {}
    if zone:
        where["zone"] = zone
    if days is not None:
        anchor = now or datetime.now().astimezone()
        where["epoch"] = {"$gte": (anchor - timedelta(days=days)).timestamp()}

    # Over-fetch so post-filtering excluded ids can't empty the result set.
    n = min(col.count(), max(limit * 3, limit + len(exclude_ids or [])))
    res = col.query(
        query_texts=[query],
        n_results=n,
        where=where or None,
        include=["documents", "metadatas", "distances"],
    )

    excluded = set(exclude_ids or [])
    out: list[dict] = []
    for rid, doc, meta, dist in zip(
        res["ids"][0], res["documents"][0], res["metadatas"][0], res["distances"][0]
    ):
        if rid in excluded:
            continue
        out.append(
            {
                "report_id": rid,
                "zone": meta["zone"],
                "timestamp": meta["timestamp"],
                "report_type": meta["report_type"],
                "severity": meta["severity"],
                "similarity": round(1.0 - float(dist), 3),
                "text": doc,
            }
        )
        if len(out) >= limit:
            break
    return out


@tool
def semantic_search(
    query: str,
    limit: int = 8,
    zone: str | None = None,
    days: int | None = None,
) -> list[dict]:
    """Find past reports describing a similar situation, however they were worded.

    Matches on meaning rather than words, so "someone hanging around the
    mailboxes" and "a person by the delivery lockers" find each other. This is
    the right tool for asking "has anything like this been reported before?".

    Leave `zone` unset unless you have a specific reason to narrow. Whether a
    group of similar reports is spread across several zones or concentrated in
    one is itself the evidence you need — filtering by zone hides exactly the
    signal that separates a real local pattern from a handful of unconnected
    incidents that happen to sound alike.

    Args:
        query: What to look for, in plain language. The text of the report you
            are assessing usually works well as the query.
        limit: How many matches to return. Defaults to 8.
        zone: Restrict to one zone. Usually leave unset — see above.
        days: Restrict to the last N days. Usually leave unset; how old the
            similar reports are is evidence you want to see, not filter out.

    Returns:
        Matches ordered most similar first, each with report_id, zone,
        timestamp, report_type, severity, the redacted text, and a similarity
        score from 0 to 1. Roughly: above 0.6 is a strong match, 0.4-0.6 is
        loose, below 0.4 is usually coincidence. An empty list means nothing
        resembling this has been reported, which is the common case.
    """
    return search(query=query, limit=limit, zone=zone, days=days)
