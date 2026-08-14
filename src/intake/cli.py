"""Submit a single report from the command line.

    python -m src.intake.cli "someone took my package from the porch" --zone "Elm St north"

This is the first thing to run against a live account. It exercises Bedrock
auth, all three model ids, structured-output parsing, persistence, and indexing
in one shot — which is where credential and inference-profile problems actually
surface, and much easier to read than the same failure on report 1 of 38.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime

from src.pipeline import StageError, submit


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m src.intake.cli",
        description="Submit one neighbourhood report to Porchlight.",
    )
    parser.add_argument("text", help="the report, in the reporter's own words")
    parser.add_argument(
        "--zone",
        required=True,
        help="coarse area label, e.g. 'Elm St north'. Never a street address.",
    )
    parser.add_argument(
        "--reporter",
        default="cli",
        help="opaque reporter id; used only to count distinct reporters",
    )
    parser.add_argument(
        "--at",
        default=None,
        help="ISO timestamp; defaults to now. Useful for replaying history.",
    )
    args = parser.parse_args(argv)

    when = datetime.fromisoformat(args.at).astimezone() if args.at else None

    try:
        result = submit(args.text, args.zone, args.reporter, when)
    except StageError as exc:
        print(f"\n  Failed in the {exc.stage} stage:\n    {exc.cause}\n", file=sys.stderr)
        if exc.stage in {"triage", "correlation", "escalation"}:
            print(
                "  If this is the first run, check the Bedrock inference-profile ids:\n"
                "    python -m src.provider --list\n",
                file=sys.stderr,
            )
        return 1

    r, s, d = result.report, result.summary, result.decision
    print(f"\n  report   {r.report_id}  [{r.report_type}, severity {r.severity}/5]")
    print(f"  zone     {r.zone}")
    print(f"  summary  {r.summary}")
    print(
        f"\n  cluster  {s.cluster_size} report(s), {s.distinct_reporters} reporter(s), "
        f"{s.time_span_hours:.0f}h, {len(s.zones_involved)} zone(s), z={s.anomaly_score:.2f}"
    )
    print(f"\n  action   {result.outcome.upper()}")
    print(f"  because  {d.reasoning}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
