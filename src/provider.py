"""Model selection, one place.

Each stage gets the smallest model that can do its job:

    triage       Haiku 4.5   typed extraction from one short report
    correlation  Sonnet 5    deciding which lookups to make and reading results
    escalation   Opus 5      the judgment call, and the only one worth Opus

Prompt caching is on for all three. A demo run makes 38 calls per agent with a
byte-identical system-prompt and tool-schema prefix, so the prefix is written
once and read 37 times at roughly a tenth of the input price. Together with the
split this is the difference between ~20 and ~55 full runs inside the credits.

Sampling parameters are deliberately absent. Opus 5 and Sonnet 5 reject
`temperature`, `top_p`, and `top_k` outright — steer with the prompt instead.
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Literal

from strands.models import BedrockModel
from strands.models.model import CacheConfig, CacheToolsConfig

Role = Literal["triage", "correlation", "escalation"]

# One definition, so .env.example and the code cannot drift apart and send you
# hunting for a model in a region where it was never enabled. Bedrock model
# availability is per-region, and "NOT FOUND" from --list reads like a
# permissions problem when it is really a geography one.
DEFAULT_REGION = "us-east-1"

# Bedrock serves Claude through inference profiles, so ids carry both a routing
# prefix ("global." or a region like "us.") and the "anthropic." vendor prefix.
#
# ⚠️ VERIFY BEFORE THE FIRST RUN. These are the expected ids, not confirmed
# ones. Run `python -m src.provider --list` (or `aws bedrock
# list-inference-profiles --region <region>`) and override via .env with what
# your account actually has. A wrong id fails at the first call, and model
# access must also be granted in the Bedrock console for each of the three.
DEFAULT_MODELS: dict[Role, str] = {
    "triage": "global.anthropic.claude-haiku-4-5",
    "correlation": "global.anthropic.claude-sonnet-5",
    "escalation": "global.anthropic.claude-opus-5",
}

# Triage emits one small structured object. Correlation and escalation write
# prose reasoning that the demo puts on screen, so they get room.
#
# ⚠️ These are sized for thinking, not just for the answer. On Sonnet 5 and
# Opus 5, adaptive thinking runs when the `thinking` parameter is omitted — a
# change from Opus 4.7/4.8, where omitting it meant no thinking — and
# max_tokens caps thinking *plus* the response together. The failure mode is
# specific and ugly: thinking eats the budget, the structured output truncates,
# `.structured_output` comes back None, and the stage raises "returned no
# structured output" on some reports and not others. Headroom is cheap;
# output tokens are only billed for what is actually generated.
MAX_TOKENS: dict[Role, int] = {
    "triage": 2048,
    "correlation": 16384,
    "escalation": 16384,
}

# 5 minutes beats 1 hour here. The dominant cost is within a single run, where
# the 38 calls are seconds apart and a 5m entry never expires — and a 5m write
# is 1.25x input where a 1h write is 2x. Re-writing once per tuning run is
# cheaper than paying the longer-lived write on every run.
CACHE_TTL = os.environ.get("FNA_CACHE_TTL", "5m")

# The minimum cacheable prefix is per-model, and it is not monotonic across
# generations — Opus 5 caches from 512 tokens, Sonnet 5 from 1024, and
# Haiku 4.5 only from 4096. A prefix below the threshold does not error; it
# silently reports cache_creation_input_tokens = 0.
#
# Measured against the current prompts:
#
#   escalation   Opus 5      ~1240 tok prefix vs 512  → caches
#   correlation  Sonnet 5    ~1690 tok prefix vs 1024 → caches
#   triage       Haiku 4.5    ~960 tok prefix vs 4096 → NEVER caches
#
# Triage is left as-is deliberately. Padding the prompt to clear 4096 tokens
# would cost more than it saves (the wasted prefix is ~960 Haiku tokens per
# report, about $0.04 across a full 38-report run) and would mean writing
# 3000 tokens of filler into the one prompt whose precision the redaction
# guarantee depends on. Recorded here so the "cache reads are landing" check
# isn't read as a bug when triage's input count stays flat.
MIN_CACHEABLE_TOKENS: dict[Role, int] = {
    "triage": 4096,
    "correlation": 1024,
    "escalation": 512,
}


def model_id(role: Role) -> str:
    """The model id for a role, with the env override applied."""
    return os.environ.get(f"FNA_MODEL_{role.upper()}", "").strip() or DEFAULT_MODELS[role]


@lru_cache(maxsize=8)
def get_model(role: Role):
    """Build the model for one pipeline stage. Cached per role.

    Reads FNA_PROVIDER (bedrock | anthropic), AWS_REGION, and the per-role
    FNA_MODEL_* overrides. Every agent takes its model from here, so switching
    provider is one environment variable rather than an edit in three files.

    Cached so the 38 reports in a demo run share one client per role rather
    than reconstructing boto sessions 114 times.
    """
    provider = os.environ.get("FNA_PROVIDER", "bedrock").strip().lower()
    mid = model_id(role)

    if provider == "anthropic":
        try:
            from strands.models.anthropic import AnthropicModel
        except ImportError as exc:  # pragma: no cover - depends on extras
            raise RuntimeError(
                "FNA_PROVIDER=anthropic needs the extra: "
                "pip install 'strands-agents[anthropic]'"
            ) from exc

        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("FNA_PROVIDER=anthropic but ANTHROPIC_API_KEY is unset.")

        # First-party ids have no routing/vendor prefix.
        bare = mid.split("anthropic.")[-1]
        return AnthropicModel(
            client_args={"api_key": api_key},
            model_id=bare,
            max_tokens=MAX_TOKENS[role],
        )

    return BedrockModel(
        model_id=mid,
        region_name=os.environ.get("AWS_REGION", DEFAULT_REGION),
        max_tokens=MAX_TOKENS[role],
        # "auto" detects Claude from the model id and places the cache point to
        # maximise coverage. cache_prompt is the deprecated spelling.
        cache_config=CacheConfig(strategy="auto", ttl=CACHE_TTL),
        cache_tools=CacheToolsConfig(type="default", ttl=CACHE_TTL),
    )


def _list_profiles() -> int:
    """Print the inference profiles this account can actually use.

    Exists because guessing a profile id is the single most likely way for the
    first run to fail, and the failure looks like a credentials problem.
    """
    region = os.environ.get("AWS_REGION", DEFAULT_REGION)
    try:
        import boto3
    except ImportError:
        print("boto3 not installed.")
        return 1

    try:
        client = boto3.client("bedrock", region_name=region)
        profiles = client.list_inference_profiles().get("inferenceProfileSummaries", [])
    except Exception as exc:
        print(f"Could not list inference profiles in {region}:\n  {exc}\n")
        print("Check AWS credentials and that the Bedrock service is available there.")
        return 1

    claude = [p for p in profiles if "anthropic" in p.get("inferenceProfileId", "").lower()]
    if not claude:
        print(f"No Anthropic inference profiles visible in {region}.")
        print("Grant model access in the Bedrock console, then re-run.")
        return 1

    print(f"Anthropic inference profiles in {region}:\n")
    for p in sorted(claude, key=lambda x: x["inferenceProfileId"]):
        print(f"  {p['inferenceProfileId']:55} {p.get('status', '')}")

    print("\nConfigured (from DEFAULT_MODELS / .env):\n")
    available = {p["inferenceProfileId"] for p in claude}
    missing = False
    for role in ("triage", "correlation", "escalation"):
        mid = model_id(role)  # type: ignore[arg-type]
        ok = "OK " if mid in available else "NOT FOUND"
        if mid not in available:
            missing = True
        print(f"  {role:12} {mid:55} {ok}")

    if missing:
        print("\nSet the missing ones in .env (FNA_MODEL_TRIAGE / _CORRELATION / _ESCALATION).")
        return 1
    return 0


if __name__ == "__main__":
    import sys

    raise SystemExit(_list_profiles() if "--list" in sys.argv else 0)
