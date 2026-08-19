---
tags: [plan, hackathon, strands, porchlight]
status: approved
created: 2026-08-12
updated: 2026-08-14
---

# Porchlight — implementation plan

> Companion to [[PROJECT_BRIEF]] and [[BRANDING]]. Read the brief first; this covers **what to build now** and where it deviates from the brief.

---

## 1. Context

The vault holds [[PROJECT_BRIEF]], [[BRANDING]], and `assets/branding/`. No code, no git repo yet.

This pass builds the **full vertical slice** — intake → triage → correlate → escalate → render — plus a published static dashboard. The reasoning: **the demo *is* the submission.** Everything scored depends on a pipeline that visibly logs one-offs silently, *declines* the near-miss, and alerts on the real cluster. Getting that running early leaves the remaining weeks for the two things the brief flags as chronic risks — prompt tuning (§13) and the video (§13).

> [!important] This changes the build: real deployment is now a goal
> Confirmed 2026-08-14 — Porchlight is intended for an actual neighborhood after the hackathon. That isn't a phase-2 footnote. The safety-relevant parts of the architecture are cheap to build in now and painful to retrofit, so they land in this pass. See [§4](#4-safety-architecture).

---

## 2. Decisions locked

| Decision | Choice | Why |
|---|---|---|
| **Orchestration** | Sequential workflow in `pipeline.py` | Strands' documented *Workflow* pattern. Three agents, three prompts, no handoff loops. The brief names multi-agent debugging as the #1 schedule risk (§13). |
| **Provider** | Amazon Bedrock (Strands default) | Uses the $50 credits; AWS-native for judging. |
| **Models** | Haiku 4.5 triage · Sonnet 5 correlation · **Opus 5** escalation | Matched to task: typed extraction / tool selection / judgment. Supersedes the earlier `claude-opus-4-8` pin — Opus 5 costs the same and is stronger at the escalation call. |
| **Prompt caching** | On, all three agents | The 38 demo calls share an identical system-prompt + tool-schema prefix. Cache reads ≈0.1× input. |
| **Embeddings** | ChromaDB default (`all-MiniLM-L6-v2`, ONNX, local) | 384-dim, local, no API key, no per-embedding cost, deterministic. |
| **Persistence** | Plain function calls in `pipeline.py`, not agent tools | Deviates from brief §5 — see [§3](#deviation-from-brief-5--confirmed). |
| **Intake** | CLI | Brief §12. |
| **Demo output** | Terminal **+** generated `out/report.html` | Renders the real correlation graph from pipeline data. |
| **Public surface** | `report.html` published to S3 as a static site | Real URL for Devpost, ~$0, read-only, nothing to abuse. |
| **Report scope** | Theft, suspicious activity, vandalism, hazard, other | Brief §12. Package theft stays the headline. |

### Cost

First-party rates — **Bedrock is priced separately, check the Bedrock pricing page before committing:**

| Model | Input / Output per Mtok |
|---|---|
| Opus 5 | $5 / $25 |
| Sonnet 5 | $3 / $15 |
| Haiku 4.5 | $1 / $5 |

Split + caching ≈ **$0.90 per full 38-report run** → roughly **55 runs inside the $50**. The all-Opus, no-caching design this replaces was ~$2.20/run (≈20 runs).

> [!warning] Two corrections to this estimate, found 2026-08-20
> **Triage never caches.** The minimum cacheable prefix is per-model and is *not* monotonic: Opus 5 caches from 512 tokens, Sonnet 5 from 1024, Haiku 4.5 only from **4096**. Triage's prefix measures ~960 tokens, so it silently reports `cache_creation_input_tokens = 0` — no error, just no cache. Correlation (~1690) and escalation (~1240) both clear their thresholds. The dollar impact is ~$0.04 per run; the real cost is that [[CHECKLIST]] §2's "confirm cache reads are landing" check will show triage's input count staying flat, which reads as a bug and isn't one. Left unpadded deliberately — see the note in `src/provider.py`.
>
> **`max_tokens` now has to cover thinking.** On Sonnet 5 and Opus 5, omitting the `thinking` parameter runs *adaptive thinking* — a change from Opus 4.7/4.8, where omitting it meant none — and `max_tokens` caps thinking plus the response together. At the original 4096 the structured output can truncate, `.structured_output` returns `None`, and the stage raises "returned no structured output" on some reports and not others. Raised to 16384 for both; output tokens are billed on what is generated, so the headroom is free.

> [!warning] Set an AWS Budget with a zero-spend alert before the first call
> It's free, and it is the only thing that catches a runaway loop during prompt tuning. Do it before step 1.

---

## 3. Architecture

```
demo/run_demo.py ─┐
src/intake/cli.py ┴→ src/pipeline.py
                        │
                        ├─ triage_agent      Haiku 4.5 · structured output → TriagedReport
                        │                    (produces redacted_text — see §4)
                        │     └─ pipeline persists: store_report + embed_and_index
                        │
                        ├─ correlation_agent Sonnet 5 · tools: semantic_search,
                        │                    check_baseline_deviation, get_zone_history
                        │
                        └─ escalation_agent  Opus 5 · tools: draft_alert, send_alert
                                             (else writes silent log)
                                 │
                    SQLite + Chroma → src/render.py → out/report.html → S3
```

> [!note] A Strands agent is a library, not a server
> `agent(prompt)` sends the system prompt, message, and tool JSON schemas to Claude via Bedrock; Claude replies with an answer or a tool call; the SDK runs your local Python function and feeds the result back; the loop repeats. No port, no daemon, no UI. **The HTML is a build artifact** — `run_demo.py` finishes, reads SQLite, writes one self-contained file. If a live web app is ever added, the route calls `process_report()` — that direction, never the reverse.

### Deviation from brief §5 — confirmed

> [!check] Approved 2026-08-12
> This stands. Brief §5's tool assignment is superseded.

- **Classification uses structured output** (`structured_output_model=TriagedReport`) rather than a tool round-trip — it's typed extraction, and structured output is more reliable.
- **Persistence runs as plain function calls in `pipeline.py`.** The failure this avoids: on report 22 of 38 the model answers without calling `embed_and_index`. That report is invisible to `semantic_search`, the cluster returns 3 instead of 4, escalation correctly declines, and **the demo's one alert never fires**. Nothing raises. Nothing logs. It just quietly produces the wrong result, on some runs.
- **The real `@tool` surface concentrates on correlation**, where the agent's judgment determines which lookups to make, and on escalation, where the tool call *is* the action.

The brief's critical rule is preserved: the escalation decision lives in the agent's **reasoning** under its system prompt, never an `if count > 3` branch. Thresholds are passed as *evidence*; `EscalationDecision.reasoning` is required so the judgment is visible on screen. That visibility is the difference between an agent and a cron job.

---

## 4. Safety architecture

Because this will be deployed to real people.

A system where residents report on neighbors, and which then *amplifies* correlated reports, has one dominant failure mode: **"suspicious person" reports are the category most prone to racial and class bias, and correlation can systematize that bias into an official-looking alert.** This is the documented failure of every product in this category — it is the reason [[BRANDING]] counter-positions against Ring and Citizen in the first place.

Four structural choices defuse most of it, and every one makes the product *better*, not more constrained.

### 4.1 Correlate on place and behavior, never on person descriptions

`TriagedReport.summary` is the triage agent's neutral one-sentence rewrite: physical descriptions, names, vehicle make/colour/plate, and street numbers stripped; **the specific place and behavior kept**. **Only the summary is embedded, stored long-term, and shown to people.** The reporter's raw words live in SQLite until they expire (§4.4) and are never indexed.

Alerts describe **a place to watch, not a person to look for.** This goes in the escalation prompt explicitly.

> [!check] Measured, not assumed — and it changed the design
> The original plan had a separate `redacted_text` holding a fuller rewrite, indexed alongside a shorter `summary`. Measurement killed that.
>
> **Indexing the fuller text fails.** On the seed cluster, the weakest cluster report ranked *below* an unrelated report under every query strategy tried — separation **−0.03 to −0.16**. Incidental narration (*"when I got back from work"*, *"again tonight"*) dominates the embedding of a short text.
>
> **Indexing the normalised sentence passes**, separating the same groups by **+0.28 to +0.52**, with cluster matches at 0.69–0.77 against unrelated topping out at 0.32.
>
> So normalisation is not a privacy tax paid at the cost of accuracy — it is *what makes retrieval work*. One field now does both jobs, which also means one redaction surface to defend instead of two.
>
> **The tradeoff it introduces:** normalise too hard and unrelated reports start to look alike. `tests/test_vectors.py::test_near_miss_stays_separable` asserts the near-miss group stays distinct from the genuine cluster (currently margin **+0.284**), so a future prompt edit can't quietly collapse them and take the video's best moment with it.

### 4.2 A cluster requires distinct reporters

`CorrelationSummary.distinct_reporters`, passed to escalation as evidence. Four reports from one person is not a pattern — it is one anxious neighbor, or one person manufacturing an alert about someone they dislike. **A correlation-quality fix and a harassment defense in the same field.**

### 4.3 Human approval before any alert leaves the system

The architecture already separates `draft_alert` from `send_alert`. Behind `FNA_REQUIRE_APPROVAL=1`, `send_alert` blocks for human confirmation. The agent notices and drafts; a person decides to send.

That is also the honest version of the pitch: *"it wakes a human"* should mean a human is in the loop, not that it broadcasts.

### 4.4 Retention window

Raw report text deleted after N days (default 90); aggregate counts survive so the per-zone baselines keep working. Baselines need counts, not narratives.

**4.1–4.3 ship in this pass** — prompt and schema work, near-zero cost now. **4.4 is a scheduled job**: stub the `raw_text_expires_at` column now, build the job in [§8](#8-phase-2--real-deployment).

> [!warning] Not legal advice — I can't give it
> Before real residents use this, get advice on: liability if an alert precedes a confrontation; whether the operator becomes a data controller under the applicable privacy regime; and whether a community group vs. a company changes that answer. Put this in the README rather than discovering it after launch.

---

## 5. Files to create

```
porchlight/
├── README.md, LICENSE (MIT), requirements.txt, .env.example, .gitignore
├── src/
│   ├── models.py          # the Pydantic contract
│   ├── provider.py        # get_model(role) — per-role model + caching
│   ├── prompts.py         # all three system prompts, together, for tuning
│   ├── agents/{triage,correlation,escalation}.py
│   ├── tools/{storage,vectors,anomaly,alerts}.py
│   ├── intake/cli.py
│   ├── render.py          # SQLite → self-contained out/report.html
│   └── pipeline.py
├── data/{seed_reports,holdout_reports,baseline_params}.json
├── demo/run_demo.py
├── scripts/publish.sh
├── assets/branding/       # already exists — see [[BRANDING]]
├── out/                   # generated, gitignored
└── tests/{test_vectors,test_redaction,test_anomaly,test_pipeline}.py
```

---

## 6. Build order

### 6.1 — `git init` + scaffold

MIT `LICENSE`. Brief §10 needs it **visible in the GitHub About section** — that's a repo setting, not just the file. Easy to miss on submission day.

`.gitignore`: `.env`, `*.db`, `chroma/`, `out/`. `out/` is generated, so it stays untracked — but commit one PNG screenshot of a good render into `assets/` for the README hero, so the repo looks right to a judge who never runs the code.

`requirements.txt`: `strands-agents`, `strands-agents-tools`, `chromadb`, `numpy`, `scipy`, `pydantic`, `pytest`.

### 6.2 — `src/models.py`

**Write this first** — it's the contract every other file codes against.

Split into what a **model generates** and what the **code assembles**. Nothing a model could get wrong, and nothing that has to be trustworthy, is left to the model — identifiers are derived deterministically, and the numbers feeding the escalation decision are counted from storage.

| Model output | Code record |
|---|---|
| `TriageResult` — `report_type`, `severity` (1–5), **`summary`** | `TriagedReport` — the above `+ report_id`, `zone`, `timestamp`, `reporter_id` |
| `CorrelationResult` — `related_report_ids`, `assessment` | `CorrelationSummary` — the above `+ cluster_size`, **`distinct_reporters`**, `time_span_hours`, `zones_involved`, `anomaly_score` |
| `EscalationDecision` — `action` (`silent_log` \| `alert`), `urgency`, `audience`, `message`, `reasoning` | — |

- `RawReport` — `text`, `zone`, `timestamp`, **`reporter_id`**
- `report_id` is a **deterministic hash** of (zone, timestamp, reporter_id, text). The renderer seeds node positions from it, so a given seed set always draws the same picture and a take can be re-shot in week six without the graph moving. It also makes re-ingesting a report idempotent.

> [!important] `distinct_reporters` is counted, never reported
> It is a safety control (§4.2), and a model-reported safety control is not a control. The correlation agent says *which* reports are related; the pipeline counts the reporters behind them.

### 6.3 — `src/provider.py`

`get_model(role)` returning the right model per role, reading `FNA_PROVIDER` / `AWS_REGION` plus per-role overrides. Configure prompt caching on the system-prompt and tool-schema prefix.

> [!warning] Verify the Bedrock inference-profile IDs — do not hardcode a guess
> Strands' Bedrock provider uses **inference-profile IDs**, and Bedrock model IDs carry an `anthropic.` prefix. Run `aws bedrock list-inference-profiles --region <region>` and use what's actually there. Confirm model access is granted in the Bedrock console **for all three models**. A guessed ID fails at first call.

### 6.4 — `src/tools/storage.py`

SQLite log. `store_report()`, `get_zone_history(zone, days)`, `write_log_entry()`. Only `get_zone_history` is `@tool`; the writes are plain functions. Schema carries `reporter_id` and `raw_text_expires_at`.

### 6.5 — `src/tools/vectors.py`

`chromadb.PersistentClient`, one collection, **default embedding function** — do *not* pass one. Pin `hnsw:space` to `cosine` so `similarity = 1 - distance` means something rather than being a guess. **Index the summary only** (§4.1).

`semantic_search(query, limit, zone=None, days=None)` is `@tool`. **Both filters default to off, and the docstring tells the agent to leave them off.** Filtering by zone would hide the near-miss entirely — those three reports are in three different zones, and the zone spread *is* the evidence that makes declining correct. A tool that filtered by default would remove the demo's best moment.

### 6.6 — `src/tools/anomaly.py`

~50 lines per brief §6. Per-zone rolling-window arrival rate, z-score against **that zone's own history**. `check_baseline_deviation(zone)` is `@tool` and returns the score *plus the counts behind it*, so correlation can reason about the number rather than trust it.

### 6.7 — `data/seed_reports.json`

> [!important] The most important file in the repo
> Fixed anchor date, deterministic, seeded.

- **One genuine cluster** — 4 reports, same zone (parcel lockers, bldg 3), ~36h, **four different `reporter_id`s**, each phrased differently. Use the brief's own set: *"guy hanging around the mailboxes"* / *"suspicious dude by the post boxes"* / *"someone loitering near the parcel lockers"*. Keyword matching must visibly fail on these.
- **~25 isolated one-offs** — spread across zones, types, weeks. All silently logged.
- **One near-miss** — 3 semantically similar reports over ~3 weeks and 3 zones. **Must be declined.** Per brief §10 this is the most persuasive moment in the video, so make declining *clearly* correct, not marginal.
- **One single-reporter pseudo-cluster** — 4 similar reports, same zone, tight window, **one `reporter_id`**. Must be declined on `distinct_reporters=1`. This is §4.2 made visible, and it's a good 15 seconds of video.
- **Baseline history** — one busy zone and one quiet zone, so the anomaly detector demonstrably treats them differently.

### 6.8 — `data/holdout_reports.json`

20 reports **never used during prompt tuning**, including two adversarial cases: a real cluster with no shared vocabulary, and three unrelated reports with heavy shared vocabulary. Run once at the end; report the result in the README honestly whatever it is.

This is a stronger credibility claim than data provenance — it tests the actual failure mode, a system tuned until it passes its own demo.

### 6.9 — `data/baseline_params.json`

Per-zone arrival-rate parameters derived from a public dataset (NYC 311 or similar). **Ship the derived aggregates, not rows** — no PII, no address data, no licensing question. Lets the README say baselines are calibrated against observed data rather than hand-tuned. Off the critical path.

### 6.10 — `src/prompts.py` + `src/agents/*.py`

One `Agent(model=get_model(role), system_prompt=..., tools=[...], name=...)` per file.

Per brief §7: **the tool docstring is the tool's only interface to the model.** Write the docstrings as carefully as the prompts — a vague docstring is a bug.

Triage prompt carries the redaction rule (§4.1). Escalation prompt carries place-not-person and treats `distinct_reporters` as evidence (§4.2).

### 6.11 — `src/pipeline.py`

`process_report(raw) -> EscalationDecision`. Triage → persist → correlate → escalate. Wrap each stage so a failure names the stage it failed in.

### 6.12 — `src/tools/alerts.py`

> [!warning] Deviation from the original plan
> The plan gave the escalation agent `draft_alert` and `send_alert` as tools. They are **plain pipeline functions** instead. `EscalationDecision` already carries action, urgency, audience, and the message text — every argument `send_alert` would take. Having the agent then call a tool with those same values adds a round-trip that can disagree with the decision it just made, and creates two paths for an alert to fire or be missed.
>
> **The agent decides. The pipeline dispatches. The human approves.** The escalation agent keeps `get_zone_history` so it can look deeper before deciding; it just doesn't hold the trigger.

`send_alert` writes to console + `alerts.log`; behind `FNA_REQUIRE_APPROVAL=1` it blocks for human confirmation (§4.3). Off for the demo, on for deployment. With approval required and no terminal attached, it **declines to send** rather than sending something nobody agreed to.

Also here: `format_line`, the one-line-per-report demo output, using the [[BRANDING]] palette — amber only ever marks an escalation.

### 6.12b — Repeat-alert suppression

Not in the original plan; found while building. Nothing stopped the pipeline re-alerting on every subsequent report that joined an already-escalated cluster. In the demo that is two alerts instead of one; in a real deployment it is what teaches a block captain to ignore you.

`storage.alert_coverage` records which reports a sent alert covers. A later cluster overlapping a covered report logs silently instead of re-alerting.

### 6.13 — Observability, from day one

Brief §7 says tracing is not optional with three agents. `pip install 'strands-agents[otel]'`, then `StrandsTelemetry().setup_console_exporter()` behind `FNA_TRACE=1` so demo output stays clean.

### 6.14 — `demo/run_demo.py`

Feeds the seed set in timestamp order, one line per report, then a summary tallying silent / declined / alerted.

`--explain` prints the full correlation summary and escalation reasoning for **the near-miss, the single-reporter case, and the real cluster** — the video's most important 30 seconds. Build it as a first-class feature, not an afterthought.

`--html out/report.html` triggers the render.

### 6.15 — `src/render.py`

One **self-contained** HTML file: inline `<style>`, inline `<svg>`, no scripts, no CDN, no build step. Double-click to open.

- **Layout seeded from `report_id`** so it's byte-identical across runs — you can re-shoot a take in week six without the picture moving.
- `--sill` `#243352` for silently-logged reports (the ~30 that make the argument by staying dark).
- Mid-tone, **visibly unlinked** nodes for the declines. This is the money shot.
- `--lamp` `#FFB454` with edges and a radial glow for the escalated cluster.
- The escalation agent's own `reasoning` beneath, in the card layout from [[BRANDING]].

> [!important] The palette rule applies here too
> Amber marks escalation and nothing else — not headings, not borders, not the summary line. See [[BRANDING]] § *Palette*. The graph is only persuasive because almost all of it is dark.

`assets/branding/02-graph-motif.png` is the target composition — `render.py` reproduces that image from live data. **Two failure modes to avoid:** don't let the layout collapse into an unreadable clump (enforce minimum node separation), and hand-place nothing — if the seed data changes, the picture must follow automatically or it stops being evidence.

### 6.16 — `scripts/publish.sh`

`aws s3 cp out/report.html s3://<bucket>/index.html` plus the bucket policy. Static website hosting; no CloudFront needed at this traffic. Note in the README that the page is generated from demo data.

---

## 7. Verification

Run in order. Each step is a real check, not a smoke test.

1. ✅ **Retrieval catches paraphrase** — `test_vectors.py`, 4 passing. Index the four differently-worded cluster reports plus the near-miss and ordinary traffic; query with a cluster report's own summary; assert every cluster report outranks every unrelated one, **and** that the near-miss stays separable. Also asserts a keyword search would fail on the raw reports, so the semantic layer is demonstrably doing real work.
   → **If this fails the project's premise fails. Stop and fix before wiring any agents.** *(It did fail on the first run — see §4.1.)*

2. **Redaction holds** — `test_redaction.py`. Feed reports containing names, plates, and street numbers; assert none survive into `summary` or the vector store. This is the §4.1 guarantee — it needs a test, not a prompt. Needs Bedrock, so it runs after the model IDs are verified.

3. ✅ **Anomaly detector discriminates** — `test_anomaly.py`, 6 passing. Identical 4-report bursts score z>3 in a zone whose baseline is 2/week and z<1 where it is 3/day. Also covers the two divide-by-zero cases a textbook z-score would hit: a zone with no history, and one with a perfectly flat rate.

4. **Pipeline runs on one report** —
   ```
   python -m src.intake.cli "someone took my package from the porch" --zone "Elm St north"
   ```
   Confirms Bedrock auth, all three model IDs, structured-output parsing, and persistence in one shot. **Do this before the full set** — it's where credential and model-ID problems surface.

5. **Full demo** — `python demo/run_demo.py`. Assert all four behaviors: one-offs silently logged, near-miss declined, single-reporter cluster declined, real cluster alerted. `test_pipeline.py` asserts this **as a test**, not just prints it, so prompt tuning can't silently regress the demo.

6. **HTML matches the terminal** — count amber nodes in the browser, assert it equals the alert count printed. Both read the same SQLite rows; a mismatch means `render.py` is filtering wrong, and a graph that contradicts the log is worse than no graph.

7. **Holdout run** — once, at the end, never during tuning. Record the result in the README.

8. **Traces** — `FNA_TRACE=1 python demo/run_demo.py`. One agent span per stage with token usage, tool spans nested under correlation. **Confirm cache reads are landing** — input token counts should drop sharply after report 1.

9. **Clean-clone check** — brief §10 requires setup instructions that work from a clean clone. Fresh venv, `pip install -r requirements.txt`, run the demo.
   → Note the **first-run ChromaDB model download (~80 MB)** in the README so it isn't mistaken for a hang.

---

## 8. Phase 2 — real deployment

Documented in the README as roadmap; built after the hackathon.

- Consent flow for reporters
- Moderation queue UI
- The retention / deletion job (§4.4)
- Per-reporter rate limiting
- False-report flagging path
- Real alert dispatch (SMS / Discord)
- AgentCore or Lambda hosting

The structural safety work (§4.1–4.3) lands in *this* pass, so phase 2 is additive rather than a rewrite.

---

## 9. Open

- **Deadline undated.** Brief says "6 weeks from project start"; today is **2026-08-14**. Confirm the Devpost deadline and back-date the week-6 video work from it.
- **Repo name** — folder is `friendly-neigh-agent`, brief §8 says `friendly-neighborhood-agent`, `porchlight` is the strongest candidate. `git init` doesn't record a name; settle it before `gh repo create`.
- **Bedrock model access** — all three models need access granted in the console; profile IDs verified, not guessed.
- **Alert recipient** — modelled as `EscalationDecision.audience`, so deciding later costs nothing.
- **Trademark constraint** — settled in [[BRANDING]] § *Trademark scope*, which supersedes the internal contradiction in [[PROJECT_BRIEF]] §11.
- **Live web app** — considered and deferred. A chatbot's synchronous, user-initiated interaction model works against the "most days it says nothing" pitch, and unauthenticated inference has no spend ceiling. Revisit post-hackathon.
