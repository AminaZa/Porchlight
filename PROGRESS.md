---
tags: [log, hackathon, porchlight]
status: active
created: 2026-08-14
---

# Progress log

> Running record of what got built, what changed, and why. Newest first.
> Companion to [[IMPLEMENTATION_PLAN]] (what we're building) and [[BRANDING]] (how it looks).

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
