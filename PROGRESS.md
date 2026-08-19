---
tags: [log, hackathon, porchlight]
status: active
created: 2026-08-14
---

# Progress log

> Running record of what got built, what changed, and why. Newest first.
> Companion to [[IMPLEMENTATION_PLAN]] (what we're building), [[BRANDING]] (how it looks), and [[CHECKLIST]] (what's left).

---

## 2026-08-20 — Redaction guard, four defects, and two model-behaviour corrections

### The redaction guard (`src/guards.py`)

§4.1 said person-identifying detail must not survive triage. The prompt asked for it and `test_redaction.py` checked it, but nothing *enforced* it — a prompt is an instruction a model may not follow, and a test tells you about the twelve cases you thought of, after the fact.

`RedactionGuard` is a Strands `HookProvider` on `AfterModelCallEvent`. It scans what the model actually produced — walking `toolUse` inputs, not just text blocks, because with `structured_output_model` that is where the summary lives — and on a hit sets `event.retry`, which discards the response and re-invokes the model before the pipeline, storage, or the index sees it. Two retries, then the report fails closed.

The retry flag is what makes this worth doing as a hook rather than a pipeline check: a pipeline check can only reject a finished result, so a leak becomes a lost report. Here it costs one Haiku call.

`tests/test_guards.py` — 32 tests. Recall against constructions a neighbour actually types, and precision against the offline fixtures and the holdout, because a guard that fires on ordinary reports is one that gets switched off.

### Four defects

- **`.env` was never loaded.** No `python-dotenv`, no `load_dotenv()` anywhere, while the README told judges to put their verified model ids there. A clean clone would edit `.env`, silently fall back to the unverified `DEFAULT_MODELS` guesses, and fail at the first Bedrock call with something that looks like a credentials error. Loading now happens in `src/__init__.py`, which every entry point imports.
- **Telemetry was documented but absent.** `FNA_TRACE` in `.env.example`, `strands-agents[otel]` in requirements, two checklist items referencing it — and no code calling `StrandsTelemetry`. `src/telemetry.py` now wires it, console by default and OTLP when an endpoint is set.
- **Region mismatch.** `provider.py` defaulted `us-west-2`, `.env.example` said `us-east-1`. Bedrock availability is per-region, so "NOT FOUND" from `--list` reads as a permissions problem when it is a geography one. One `DEFAULT_REGION` constant now.
- **`alerts.write_log` was a no-op** that deleted its arguments and returned. It was the approval-declined path's only record. Replaced with a real log line marking the draft and the refusal.

### The demo crashed when piped, on Windows

`UnicodeEncodeError` before report 1: Python takes stdout's encoding from the console code page, which is cp1252 by default, and the banner is box-drawing characters. Only visible when output is piped or redirected — which is what a screen recorder or a CI job does. Both entry points reconfigure stdout to UTF-8 now. This would have surfaced during video recording.

### Two model-behaviour corrections

Checked the request configuration against current model behaviour rather than assuming it carried over:

- **Triage never caches, and that is fine.** The minimum cacheable prefix is per-model and not monotonic across generations — Opus 5 caches from 512 tokens, Sonnet 5 from 1024, Haiku 4.5 only from 4096. Measured prefixes: escalation ~1240, correlation ~1690, triage ~960. Triage silently reports zero cache creation. Worth ~$0.04 a run, so it stays unpadded; the point of recording it is that [[CHECKLIST]] §2's cache check will show triage flat and that is not a bug.
- **`max_tokens` has to cover thinking now.** On Sonnet 5 and Opus 5, omitting the `thinking` parameter runs adaptive thinking — the opposite of Opus 4.7/4.8, where omitting it meant none — and `max_tokens` bounds thinking and response together. At 4096 the structured output can truncate, `.structured_output` returns `None`, and the stage raises "returned no structured output" intermittently. Raised to 16384 for both. Not yet observed, because nothing has run against a real model — this is a prediction, and the first live run is where it gets tested.

**52 tests green** (was 20), 13 live redaction tests still waiting on credentials. Offline demo unchanged at 38 · 31 silent · 5 declined · 1 suppressed · 1 alert.

---

## 2026-08-14 (evening) — First full demo run

Ran the whole seed set through the pipeline in offline mode. **38 reports · 31 silent · 5 declined · 1 suppressed · 1 alert.** The parcel-locker cluster escalates once; report 38 joins it and is correctly suppressed rather than re-alerting.

Two defects surfaced, neither of which the test suite caught — both found by running it and looking at the output.

### Four nodes were rendering as two

All four escalated nodes were lit and all six edges drawn, so the *data* was right. But two pairs sat **3.35px and 7.61px apart** with radii of 6.5, so they overlapped into single blobs. The page was visually understating the evidence the alert rested on.

Self-inflicted: when the layout was rewritten to fix clumping, cluster members ended up placed at random angles around their centroid with no separation check. They now sit at evenly spaced angles with bounded jitter, and the radius is derived from the chord length needed to keep neighbours `MIN_SEP` apart. Nodes are now 61–92px apart.

`test_no_two_nodes_overlap` asserts it, because this is exactly the class of bug a suite should catch.

### The stub explained a decline wrongly

It checked corroboration before time span, so two package thefts **478 hours apart** were declined for "only 2 reporters" — and the text read *"one person's concern"* when there were two people. It now names whichever condition actually decided, most decisive first:

- *"2 similar reports, but 20 days apart. Too far apart to be one ongoing situation."*
- *"3 similar reports, all from the same person. One neighbour's repeated concern is not corroboration."*
- *"3 reports from 3 different people, all in one zone, inside 13 hours, in a place that normally sees far less (z=6.5)."*

> [!note] Both of these were found by looking, not by testing
> The retrieval failure, the suppression coverage bug, the ALERT/suppressed contradiction, the overlapping nodes — every significant defect this session came from running the thing and reading the output, not from the suite. The suite is what stops them coming back.

### Added [[CHECKLIST]]

Everything outstanding, in dependency order, with the brief's §10 submission items transcribed exactly. Two of those had been slipping through unnoticed: **AWS Builder ID** and the **builder.aws.com bonus post**.

---

## 2026-08-14 (later) — Offline mode, and the finding that justifies the whole design

### A similarity threshold cannot do this job

Building the offline demo forced a measurement that turned out to be the strongest evidence in the project.

| | cosine similarity |
|---|---|
| Within the genuine cluster | 0.708 – 0.814 |
| **Within the near-miss** | **0.436 – 0.456** |
| **Near-miss report → an unrelated report** | **0.576** |

The near-miss reports resemble each other *less* than one of them resembles a completely unrelated report about a car driving past some driveways. A threshold sweep confirms there is no escape:

| threshold | correct near-miss links | wrong cross-group links |
|---|---|---|
| 0.40 | 6 | 60 |
| 0.45 | 2 | 20 |
| 0.50+ | 0 | — |

> [!important] This is the argument for the product
> Telling *"three people described loitering in three zones over three weeks"* apart from *"these two sentences both mention driveways"* requires **reading** them and weighing where, when, and who reported. That is why there is an agent here and not an `if similarity > x` branch — and now it's measured rather than asserted. It's in the README.

Consequence: `--offline` **cannot** reproduce the near-miss decline, and that is correct rather than a gap to paper over. A stub with no judgment cannot demonstrate judgment. Documented loudly in `demo/offline.py` and in the banner.

### Built

- **`demo/offline.py` + `--offline`** — the pipeline runs with no AWS account and no spend. Only the three model calls are stubbed; retrieval, anomaly detection, evidence counting, suppression and rendering are all real.
  Labelled on every surface: terminal banner, closing reminder, and a band across the top of the generated page. `scripts/publish.sh` **refuses** to publish an offline-generated report.
- **`demo/offline_fixtures.json`** — hand-written triage output for all 38 seed reports.
- **`data/holdout_reports.json`** — 20 reports, written *before* any tuning began, with two adversarial cases: a real 4-report cluster whose reporters share almost no vocabulary, and four reports about parked cars on one street that are four unrelated incidents.
- **`scripts/publish.sh`** — S3 static publish, creates the bucket and policy on first run.
- **`tests/test_redaction.py`** — 13 tests, skipped unless `FNA_LIVE_TESTS=1`, so the default suite stays free and offline.

### Another bug the demo output caught

`format_line` checked `action == "alert"` before checking `suppressed`, so report 38 printed **▲ ALERT** while the tally counted it as suppressed — the terminal contradicting itself in the same frame. Suppression is now checked first.

### Architecture diagram corrected

`assets/architecture.html` had drifted from the code. One item was a genuine contradiction: escalation was shown holding `draft_alert` and `send_alert`, when its only tool is `get_zone_history`. Four references to the removed `redacted_text` field also fixed, and three real behaviours added that the diagram never showed — computed-not-reported counts, repeat-alert suppression, and the measured reason for indexing the summary.

---

## 2026-08-14 — Vertical slice built and green

**Where it stands:** every part of the pipeline that can be built and tested without AWS credentials is done and passing. **19 tests green.** Nothing has yet been run against a real model.

### Built

| | |
|---|---|
| `src/models.py` | The contract. Result models (model-generated) split from record models (code-assembled). |
| `src/provider.py` | `get_model(role)` — Haiku 4.5 / Sonnet 5 / Opus 5, prompt caching on all three. `--list` verifies Bedrock profile ids. |
| `src/prompts.py` | The three system prompts, together, for tuning. |
| `src/agents/*.py` | triage · correlation · escalation. |
| `src/tools/*.py` | storage (SQLite) · vectors (ChromaDB) · anomaly (per-zone z) · alerts (dispatch + demo output). |
| `src/pipeline.py` | Sequential workflow, stage-named errors, evidence computed here. |
| `src/render.py` | SQLite → one self-contained HTML file, deterministic seeded layout. |
| `src/intake/cli.py` | Single-report entry point. |
| `demo/run_demo.py` | The full run, `--explain`, `--html`. |
| `data/seed_reports.json` | 38 reports. Composition verified. |
| `tests/` | 19 passing. |

### Three findings that changed the design

**1. Indexing raw report text does not work.** *(This is the significant one.)*

The first run of the premise check failed. The weakest cluster report ranked **below an unrelated report** — separation **−0.03 to −0.16** across every query strategy tried, including querying with a report's own text.

Cause: incidental narration ("when I got back from work", "again tonight", "probably nothing") dominates a 384-dim embedding of a short text.

Indexing the **normalised triage summary** instead separates the same groups by **+0.28 to +0.52** — cluster matches at 0.69–0.77, unrelated topping out at 0.32.

Consequence: `summary` and `redacted_text` merged into one field. Normalisation is not a privacy tax paid against accuracy — it is *what makes retrieval work*. It also leaves one redaction surface to defend instead of two.

Risk it introduces: normalise too hard and unrelated reports start to look alike. `test_near_miss_stays_separable` asserts the near-miss stays distinct from the genuine cluster (margin currently **+0.284**), so a future prompt edit can't quietly collapse them.

**2. Nothing suppressed repeat alerts.** Every subsequent report joining an already-escalated cluster would alert again. In the demo that's two alerts instead of one; in deployment it's what teaches a block captain to ignore you. Added `alert_coverage`.

**3. Two bugs the rendered page caught that the test suite did not.** Both from one root cause — suppression didn't record the suppressed report as *covered* by its alert:

- the graph drew a four-report cluster as three, since only covered nodes are lit
- the suppressed duplicate passed the "genuine decline" filter and took the card slot meant for the near-miss, so the page restated the alert instead of showing the decline the product exists to demonstrate

Found by screenshotting the page and looking at it. Both now have regression tests.

> [!note] Worth remembering
> A third bug — the database recording `action="alert"` for suppressed reports, so the page counted two alerts where the terminal printed one — was caught by verification step 6 on its first run. That step exists precisely because *a graph that contradicts the log is worse than no graph*, and it earned its place immediately.

### Deviations from the plan, all deliberate

- **Result models split from record models.** `report_id` is a deterministic hash, not model-generated — the renderer seeds node positions from it, so a model-invented id would make the graph move between takes. `zone`/`timestamp`/`reporter_id` are echoed from the raw report rather than re-derived.
- **Correlation returns ids and prose, never counts.** `cluster_size`, `distinct_reporters`, `time_span_hours`, `zones_involved` are counted from storage. `distinct_reporters` is a safety control and a model-reported control is not a control.
- **Alerts dispatch from the pipeline, not as agent tools.** `EscalationDecision` already carries every argument `send_alert` would take; a tool call with the same values can disagree with the decision that produced it. The agent decides, the pipeline dispatches, the human approves.
- **`semantic_search` filters default to off**, and the docstring says to leave them off. Filtering by zone would hide the near-miss entirely — those three reports are in three zones, and the spread *is* the evidence.

### GitHub

**https://github.com/AminaZa/Porchlight** — public, MIT license detected by GitHub (brief §10 satisfied), 8 topics, default branch `main`.

The repo already existed as an empty placeholder created 2026-08-12, so the work was pushed into it rather than creating a second one. Both early commits were reauthored from a placeholder identity to `AminaZa <za.amina2005@gmail.com>`. `.obsidian/` and `Notes.md` are kept local.

### Blocked

Only one thing, and it is **AWS credentials, not the `aws` CLI**. `python -m src.provider --list` runs on boto3, which is already installed — it needs credentials in the environment or `~/.aws/credentials`, nothing else.

- Bedrock inference-profile ids unverified.
- Bedrock **model access** must be granted in the console for all three models (Haiku 4.5, Sonnet 5, Opus 5) in the target region.

---

## 2026-08-12 — Branding and plan

- [[BRANDING]] settled: **Porchlight**, *your friendly neighborhood agent*. Amber-on-dusk palette, Concept B mark, eight rendered brand assets in `assets/branding/`.
- Trademark scope resolved — supersedes the internal contradiction in [[PROJECT_BRIEF]] §11, which bans "Spidey" and then offers it as safe four lines later.
- [[IMPLEMENTATION_PLAN]] approved: sequential workflow, Bedrock, ChromaDB local embeddings, CLI intake, static S3 dashboard.
- **Real deployment confirmed as a goal**, which pulled the safety architecture (§4) forward into this pass rather than leaving it to phase 2.
- Model split (Haiku/Sonnet/Opus 5) + prompt caching adopted: ~$0.90 per 38-report run instead of ~$2.20, so ~55 runs inside the $50 rather than ~20.
