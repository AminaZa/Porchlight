"""SQLite report log.

Writes are plain functions called by the pipeline, not agent tools. An agent
that "forgets" to persist a report leaves it invisible to every later search,
and the failure is silent — the cluster comes back one short, the escalation
agent correctly declines, and nothing anywhere raises. See
IMPLEMENTATION_PLAN.md §3.

Only ``get_zone_history`` is exposed to a model.
"""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

from strands import tool

from src.models import EscalationDecision, TriagedReport

DB_PATH = Path(os.environ.get("FNA_DB_PATH", "porchlight.db"))
RETENTION_DAYS = int(os.environ.get("FNA_RETENTION_DAYS", "90"))

_SCHEMA = """
CREATE TABLE IF NOT EXISTS reports (
    report_id           TEXT PRIMARY KEY,
    zone                TEXT NOT NULL,
    timestamp           TEXT NOT NULL,
    reporter_id         TEXT NOT NULL,
    report_type         TEXT NOT NULL,
    severity            INTEGER NOT NULL,
    -- The redacted, normalised sentence. The only long-lived version of the
    -- report: indexed, searched, and shown to people.
    summary             TEXT NOT NULL,
    -- The reporter's original words, kept only until they expire, then blanked.
    -- Never indexed. Aggregates and summary survive so baselines keep working.
    raw_text            TEXT,
    raw_text_expires_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_reports_zone ON reports(zone);
CREATE INDEX IF NOT EXISTS idx_reports_ts   ON reports(timestamp);

CREATE TABLE IF NOT EXISTS decisions (
    report_id          TEXT PRIMARY KEY REFERENCES reports(report_id),
    action             TEXT NOT NULL,
    urgency            TEXT,
    audience           TEXT,
    message            TEXT,
    reasoning          TEXT NOT NULL,
    -- What the agent decided vs what actually happened. An alert suppressed as
    -- a duplicate keeps action='alert' for the audit trail, but must not be
    -- drawn or counted as one — the picture has to agree with the terminal.
    suppressed         INTEGER NOT NULL DEFAULT 0,
    cluster_size       INTEGER NOT NULL,
    distinct_reporters INTEGER NOT NULL,
    time_span_hours    REAL NOT NULL,
    anomaly_score      REAL NOT NULL,
    related_ids        TEXT NOT NULL,
    decided_at         TEXT NOT NULL
);

-- Which reports are already covered by a sent alert. Prevents re-alerting on
-- every subsequent report that joins an existing cluster — a deployment that
-- does that trains its recipients to ignore it.
CREATE TABLE IF NOT EXISTS alert_coverage (
    report_id  TEXT PRIMARY KEY,
    alert_key  TEXT NOT NULL,
    alerted_at TEXT NOT NULL
);
"""


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create tables if they don't exist. Safe to call repeatedly."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with connect() as conn:
        conn.executescript(_SCHEMA)


def store_report(report: TriagedReport, raw_text: str) -> None:
    """Persist a triaged report. Idempotent on report_id."""
    expires = (report.timestamp + timedelta(days=RETENTION_DAYS)).isoformat()
    with connect() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO reports
               (report_id, zone, timestamp, reporter_id, report_type, severity,
                summary, raw_text, raw_text_expires_at)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (
                report.report_id,
                report.zone,
                report.timestamp.isoformat(),
                report.reporter_id,
                report.report_type,
                report.severity,
                report.summary,
                raw_text,
                expires,
            ),
        )


def _row_to_report(row: sqlite3.Row) -> TriagedReport:
    return TriagedReport(
        report_id=row["report_id"],
        zone=row["zone"],
        timestamp=datetime.fromisoformat(row["timestamp"]),
        reporter_id=row["reporter_id"],
        report_type=row["report_type"],
        severity=row["severity"],
        summary=row["summary"],
    )


def get_reports(report_ids: list[str]) -> list[TriagedReport]:
    """Fetch reports by id. Unknown ids are skipped rather than raising."""
    if not report_ids:
        return []
    placeholders = ",".join("?" * len(report_ids))
    with connect() as conn:
        rows = conn.execute(
            f"SELECT * FROM reports WHERE report_id IN ({placeholders})", report_ids
        ).fetchall()
    return [_row_to_report(r) for r in rows]


def zone_timestamps(zone: str) -> list[datetime]:
    """Every report timestamp for a zone. Used by the anomaly baseline."""
    with connect() as conn:
        rows = conn.execute(
            "SELECT timestamp FROM reports WHERE zone = ?", (zone,)
        ).fetchall()
    return [datetime.fromisoformat(r["timestamp"]) for r in rows]


def record_decision(
    report_id: str,
    decision: EscalationDecision,
    summary,
    suppressed: bool = False,
) -> None:
    """Log what was decided, whether it was acted on, and the evidence behind it."""
    with connect() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO decisions
               (report_id, action, urgency, audience, message, reasoning,
                suppressed, cluster_size, distinct_reporters, time_span_hours,
                anomaly_score, related_ids, decided_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                report_id,
                decision.action,
                decision.urgency,
                decision.audience,
                decision.message,
                decision.reasoning,
                int(suppressed),
                summary.cluster_size,
                summary.distinct_reporters,
                summary.time_span_hours,
                summary.anomaly_score,
                ",".join(summary.related_report_ids),
                datetime.now().astimezone().isoformat(),
            ),
        )


def cluster_already_alerted(report_ids: list[str]) -> bool:
    """True if any report in this cluster is already covered by a sent alert.

    The suppression rule for repeat alerts: once a situation has been escalated,
    a later report joining the same situation is logged rather than re-alerted.
    """
    if not report_ids:
        return False
    placeholders = ",".join("?" * len(report_ids))
    with connect() as conn:
        row = conn.execute(
            f"SELECT 1 FROM alert_coverage WHERE report_id IN ({placeholders}) LIMIT 1",
            report_ids,
        ).fetchone()
    return row is not None


def mark_cluster_alerted(report_ids: list[str], alert_key: str) -> None:
    """Record that these reports are covered by a sent alert."""
    now = datetime.now().astimezone().isoformat()
    with connect() as conn:
        conn.executemany(
            "INSERT OR REPLACE INTO alert_coverage (report_id, alert_key, alerted_at) VALUES (?,?,?)",
            [(rid, alert_key, now) for rid in report_ids],
        )


def expire_raw_text(now: datetime | None = None) -> int:
    """Blank raw report text past its retention date. Returns rows affected.

    Aggregates and redacted_text are untouched, so per-zone baselines keep
    working. Phase 2 runs this on a schedule; for now it exists so the
    retention policy is real rather than aspirational.
    """
    cutoff = (now or datetime.now().astimezone()).isoformat()
    with connect() as conn:
        cur = conn.execute(
            "UPDATE reports SET raw_text = NULL "
            "WHERE raw_text IS NOT NULL AND raw_text_expires_at <= ?",
            (cutoff,),
        )
        return cur.rowcount


def rendered_rows() -> list[dict]:
    """Every report with the decision it produced, oldest first.

    The renderer's only input. Reads the same rows the terminal printed, so the
    two cannot disagree about what happened — verification step 6 asserts they
    don't.
    """
    with connect() as conn:
        rows = conn.execute(
            """SELECT r.report_id, r.zone, r.timestamp, r.report_type, r.severity,
                      r.summary,
                      d.action, d.urgency, d.audience, d.message, d.reasoning,
                      d.suppressed,
                      d.cluster_size, d.distinct_reporters, d.time_span_hours,
                      d.anomaly_score, d.related_ids,
                      (SELECT 1 FROM alert_coverage a WHERE a.report_id = r.report_id)
                        AS covered
               FROM reports r
               LEFT JOIN decisions d ON d.report_id = r.report_id
               ORDER BY r.timestamp ASC"""
        ).fetchall()

    out = []
    for r in rows:
        related = [x for x in (r["related_ids"] or "").split(",") if x]
        decided = r["action"] or "silent_log"
        suppressed = bool(r["suppressed"])
        out.append(
            {
                "report_id": r["report_id"],
                "zone": r["zone"],
                "timestamp": r["timestamp"],
                "report_type": r["report_type"],
                "severity": r["severity"],
                "summary": r["summary"],
                # What was decided, kept for the audit trail...
                "decided_action": decided,
                "suppressed": suppressed,
                # ...and what actually happened, which is what gets drawn.
                "action": "silent_log" if suppressed else decided,
                "urgency": r["urgency"],
                "audience": r["audience"],
                "message": r["message"] or "",
                "reasoning": r["reasoning"] or "",
                "cluster_size": r["cluster_size"] or 1,
                "distinct_reporters": r["distinct_reporters"] or 1,
                "time_span_hours": r["time_span_hours"] or 0.0,
                "anomaly_score": r["anomaly_score"] or 0.0,
                "related_ids": related,
                "covered": bool(r["covered"]),
            }
        )
    return out


@tool
def get_zone_history(zone: str, days: int = 30) -> list[dict]:
    """Look up every report logged for one zone over a recent period.

    Use this when you need the full picture for a place rather than reports
    that merely resemble each other — for example to see whether a zone has a
    standing problem, or to check what else has been happening nearby.

    This returns reports by LOCATION regardless of wording. To find reports
    that describe a similar situation, use semantic_search instead.

    Args:
        zone: The zone label, exactly as it appears on a report.
        days: How far back to look. Defaults to 30.

    Returns:
        A list of reports, oldest first, each with report_id, timestamp,
        report_type, severity, and the redacted text. Reporter identity is not
        included. An empty list means this zone has no history in the period,
        which is itself worth knowing.
    """
    with connect() as conn:
        rows = conn.execute(
            "SELECT report_id, timestamp, report_type, severity, summary "
            "FROM reports WHERE zone = ? ORDER BY timestamp ASC",
            (zone,),
        ).fetchall()

    if not rows:
        return []

    latest = datetime.fromisoformat(rows[-1]["timestamp"])
    cutoff = latest - timedelta(days=days)
    return [
        {
            "report_id": r["report_id"],
            "timestamp": r["timestamp"],
            "report_type": r["report_type"],
            "severity": r["severity"],
            "text": r["summary"],
        }
        for r in rows
        if datetime.fromisoformat(r["timestamp"]) >= cutoff
    ]
