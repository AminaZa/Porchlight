"""Feed the seed set through the pipeline and show what it decided.

    python demo/run_demo.py                      # the run
    python demo/run_demo.py --explain            # + reasoning for the key cases
    python demo/run_demo.py --html out/report.html

This is the submission's centrepiece: thirty-odd reports scroll past being
logged silently, two clusters are correlated and deliberately declined, and one
alert fires.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def _utf8_stdout() -> None:
    """Make the box-drawing characters survive a Windows console.

    Python picks the console's code page for stdout, and on a default Windows
    install that is cp1252, which cannot encode ─ │ ▲ or any of the banner. The
    failure is a UnicodeEncodeError before the first report is processed, and
    it appears the moment output is piped or redirected — including when a
    screen recorder or a CI job captures it. Reconfiguring here rather than
    asking everyone to set PYTHONIOENCODING keeps the clean-clone instructions
    honest.
    """
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


_utf8_stdout()

from src import render, telemetry  # noqa: E402
from src.guards import RedactionViolation  # noqa: E402
from src.models import RawReport  # noqa: E402
from src.pipeline import Processed, StageError, process_report  # noqa: E402
from src.tools import alerts, storage, vectors  # noqa: E402

SEED = ROOT / "data" / "seed_reports.json"


def load_seed() -> list[tuple[dict, RawReport]]:
    data = json.loads(SEED.read_text(encoding="utf-8"))
    rows = sorted(data["reports"], key=lambda r: r["timestamp"])
    return [
        (
            row,
            RawReport(
                text=row["text"],
                zone=row["zone"],
                reporter_id=row["reporter_id"],
                timestamp=datetime.fromisoformat(row["timestamp"]),
            ),
        )
        for row in rows
    ]


def fresh_state() -> None:
    """Start from nothing so the run is reproducible."""
    db = Path(os.environ.get("FNA_DB_PATH", "porchlight.db"))
    if db.exists():
        db.unlink()
    vectors.reset()
    storage.init_db()


def explain(results: list[Processed]) -> None:
    """The video's most important thirty seconds."""
    interesting = [r for r in results if r.decision.action == "alert" or r.summary.cluster_size > 1]
    if not interesting:
        print("\n  Nothing correlated in this run.\n")
        return

    print("\n" + "─" * 74)
    print("  Why it decided what it decided")
    print("─" * 74)

    seen: set[str] = set()
    for res in interesting:
        key = ",".join(sorted([res.report.report_id, *res.summary.related_report_ids]))
        if key in seen:
            continue
        seen.add(key)

        s, d = res.summary, res.decision
        print(f"\n  {res.report.zone}  —  {res.outcome.upper()}")
        print(f"    {res.report.summary}")
        print(
            f"    evidence: {s.cluster_size} reports · {s.distinct_reporters} "
            f"reporters · {s.time_span_hours:.0f}h · {len(s.zones_involved)} zone(s) "
            f"· z={s.anomaly_score:.1f}"
        )
        print(f"    correlation: {s.assessment}")
        print(f"    decision:    {d.reasoning}")
    print()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="run_demo.py")
    parser.add_argument("--explain", action="store_true",
                        help="print correlation and escalation reasoning for the key cases")
    parser.add_argument("--html", nargs="?", const="out/report.html", default=None,
                        help="also write the run report to this path")
    parser.add_argument("--keep", action="store_true",
                        help="append to the existing database instead of starting fresh")
    parser.add_argument("--offline", action="store_true",
                        help="stub the three model calls so the pipeline runs with no "
                             "AWS account. NOT the agents — see demo/offline.py.")
    args = parser.parse_args(argv)

    if telemetry.setup():
        print("\n  [FNA_TRACE=1 — OpenTelemetry spans to console]")

    if args.offline:
        from demo import offline
        offline.install()
        render.OFFLINE = True
        print(offline.BANNER)

    seed = load_seed()
    if not args.keep:
        fresh_state()

    mode = "  [OFFLINE — stubbed models]" if args.offline else ""
    print(f"\n  Porchlight — {len(seed)} reports{mode}\n")

    results: list[Processed] = []
    blocked = 0
    for i, (_, raw) in enumerate(seed, start=1):
        try:
            res = process_report(raw)
        except StageError as exc:
            if isinstance(exc.cause, RedactionViolation):
                # The guard refused this report's output. That is a working
                # control, not a broken run — log it and keep going, because
                # one blocked report should not cost the other thirty-seven.
                blocked += 1
                print(f"  [{i:02d}/{len(seed)}]  blocked by the redaction guard "
                      f"— {exc.cause.findings[0][0]}")
                continue
            print(f"\n  Failed on report {i} in the {exc.stage} stage:\n    {exc.cause}\n",
                  file=sys.stderr)
            if exc.stage in {"triage", "correlation", "escalation"}:
                print("  Check the Bedrock inference-profile ids:\n"
                      "    python -m src.provider --list\n", file=sys.stderr)
            return 1

        results.append(res)
        print("  " + alerts.format_line(
            i, len(seed), res.report, res.decision, res.summary, res.suppressed
        ))

    sent = sum(r.outcome == "alert" for r in results)
    suppressed = sum(r.outcome == "suppressed" for r in results)
    declined = sum(r.outcome == "declined" for r in results)
    silent = sum(r.outcome == "silent" for r in results)

    print("\n  " + "─" * 58)
    tail = f" · {suppressed} suppressed" if suppressed else ""
    tail += f" · {blocked} blocked" if blocked else ""
    print(f"  {len(results)} reports · {silent} silent · {declined} declined{tail} "
          f"· {sent} alert{'' if sent == 1 else 's'}\n")

    if args.explain:
        explain(results)

    if args.html:
        path = render.write(args.html)
        print(f"  wrote {path}\n")

    if args.offline:
        print("  Reminder: the judgment above came from a hard-coded rule, not\n"
              "  from Opus. Run without --offline before recording anything.\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
