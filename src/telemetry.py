"""OpenTelemetry tracing, behind FNA_TRACE.

The brief calls tracing "not optional" with three agents in a chain, and the
reason is specific: when report 22 of 38 comes out wrong, the question is
always *which stage* — did triage write a vague summary, did correlation fail
to search, or did escalation weigh the evidence differently? Console spans
answer that in one run.

Off by default because the spans are far longer than the demo output they would
be interleaved with, and the demo output is what the video shows.

Two things worth watching in the spans, both of which are claims this project
makes and should therefore be able to demonstrate:

* **Cache reads.** Input token counts should fall sharply after the first
  report. The whole per-run cost estimate rests on the 38 calls sharing a
  cached system-prompt and tool-schema prefix.
* **Tool selection.** Correlation's tool spans show whether the agent actually
  left the zone and days filters alone, as its prompt and the tool docstring
  both tell it to. If it starts filtering by zone, the near-miss stops being
  visible and the demo's best moment quietly disappears.
"""

from __future__ import annotations

import os

_started = False


def enabled() -> bool:
    return os.environ.get("FNA_TRACE", "").strip() in {"1", "true", "yes"}


def setup() -> bool:
    """Start console tracing if FNA_TRACE is set. Returns whether it started.

    Safe to call more than once and safe to call when the otel extra is not
    installed — tracing is a debugging aid, and failing to trace should never
    take down a run that would otherwise have worked.
    """
    global _started
    if _started or not enabled():
        return False

    try:
        from strands.telemetry import StrandsTelemetry
    except ImportError:
        print(
            "FNA_TRACE is set but the otel extra is missing.\n"
            "  pip install 'strands-agents[otel]'"
        )
        return False

    telemetry = StrandsTelemetry()
    if os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT"):
        # An endpoint is configured, so send there rather than flooding the
        # terminal — this is the path a real deployment would use.
        telemetry.setup_otlp_exporter()
    else:
        telemetry.setup_console_exporter()

    _started = True
    return True
