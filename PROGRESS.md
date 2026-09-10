---
tags: [log, hackathon, porchlight]
status: active
created: 2026-08-14
---

# Progress log

> Running record of what got built, what changed, and why. Newest first.
> Companion to [[IMPLEMENTATION_PLAN]] (what we're building), [[BRANDING]] (how it looks), and [[CHECKLIST]] (what's left).

---

## 2026-08-21 — The alert recipient, decided; two builder posts drafted

### Alerts broadcast to the zone's residents

[[CHECKLIST]] §5 had carried this as an open question since 2026-08-14, framed as
*"single block captain vs channel broadcast"*. Reading the code first changed the
question: `Audience` was already a three-value `Literal` — `block_captain`,
`zone_residents`, `all_residents` — and the `ESCALATION` prompt said **nothing**
about it. The model was choosing among three recipients on the strength of one line
of field description, and `demo/offline.py` hard-coded `block_captain` anyway, so
the tier visible on camera was fixed regardless of what the model picked.

**Decided: broadcast to `zone_residents`.** Not `all_residents` — the alert names a
place, and sending "watch the Elm St lockers" to the whole neighbourhood is broadcast
past the point where any recipient can act on it.

`Audience` is now **single-valued**. That is the part worth keeping: the escalation
agent decides *whether* to alert and writes the message, but it cannot decide who
hears it. Widening the blast radius is a code change someone reviews, not a token a
model emits. The field also carries a default now, so the model never has to produce
it at all.

Broadcasting is the higher-risk option and was taken with that understood. Under a
single named recipient, that person is themselves a human check standing between the
model and the neighbourhood; broadcasting removes it. Three changes follow from that:

- **`ESCALATION` rewritten around the reader.** The prompt now states that the message
  goes to everyone in the zone, that **the person who was reported is likely among the
  people reading it**, and that no recipient has seen the underlying reports or the
  reasoning — the message is all they get. It forbids any wording that reads as an
  instruction to *confront, follow, record, or identify* somebody, and names the
  reasonable action instead: be aware, secure your own property, report what you see.
- **`requires_approval()` matters more, not less.** `FNA_REQUIRE_APPROVAL` is now the
  *only* human check on the path. Documented in the docstring so a future reader does
  not switch it off as ceremony.
- **The redaction guarantee gets harder, not softer.** `tests/test_redaction.py`'s
  docstring updated: the redacted sentence is now broadcast to a zone, not shown to one
  volunteer.

`render_alert` prints `· to {zone} residents` instead of the audience token, which
also reads better in the demo than `to block captain` did.

**52 tests still green**, 13 live redaction tests still skipped pending credentials.

### Builder posts 1 and 2 drafted

Both in `posts/`, neither needed AWS. The bonus is 0.2 each, up to +0.6, and scores
only when **published** on builder.aws.com before the deadline — so both checklist
boxes stay unticked.

- **Post 1** (~950 words) — the retrieval failure. Premise check failing on the first
  run, −0.03 to −0.16 separation, and redaction turning out to be *what makes retrieval
  work* rather than a tax paid against it.
- **Post 2** (~800 words) — why a similarity threshold can't do this. Built on the fact
  that the **ordering is inverted**: the near-miss reports resemble each other (0.436–0.456)
  *less* than one of them resembles an unrelated report about a car (0.576), so no cut
  point exists anywhere on the sorted list. Carries the sweep table and answers the fair
  counter-argument ("add rules on top of the threshold") rather than strawmanning it.
  One `⟨PENDING⟩`: the back-link to post 1's URL.

### Housekeeping

Three stale lines cut from [[CHECKLIST]] — the "4 commits unpushed" callout, "nothing is
on GitHub yet", and the `Push the 4 local commits` task. All three were false as of the
2026-08-20 push; `main` is level with `origin/main`. Day counts rolled 25 → 24.

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

### The deadline, finally

**14 September 2026, 5:00pm PT.** [[CHECKLIST]] §5 had it as an open question and [[PROJECT_BRIEF]] §18 guessed "six weeks from project start"; it was in the official rules the whole time. From 2026-08-20 that is **25 days**, not six weeks. The AWS credits form closes earlier, 11 September at 12pm PT.

Also from the rules: the `#AgentsforHumans` hashtag requirement was **removed** in the 2026-08-12 update. The title should still use the phrase; the hashtag is no longer required. [[PROJECT_BRIEF]] §10 is out of date on this.

### Submission copy drafted

Both of the text deliverables are written and neither needed AWS:

- **[[VIDEO_SCRIPT]]** — beat sheet, narration budgeted at ~630 words, on-screen direction. The demo section gets 2:15 of the 5:00 and is built around the two *declines* rather than the alert. §1, §2 and §4 are recordable with no live run; only the pipeline footage isn't.
- **[[DEVPOST]]** — elevator pitch, the standard form sections, tag list. Three claims that depend on the first real run are marked `⟨PENDING⟩` rather than written speculatively: the holdout result, the live demo URL, the video link.

### Blocked, and on what

AWS account verification is running, roughly 72 hours, so credentials land around **23 August**. Everything in [[CHECKLIST]] §1–§3 waits on it.

Worth recording that the credits are **not critical**, since it would be easy to treat them as a blocker: without them the entire remaining project is on the order of $20–50 of Bedrock usage. `provider.py` also still supports `FNA_PROVIDER=anthropic` as a fallback, though using it would throw away the AWS-native architecture points this hackathon explicitly rewards.

**4 commits unpushed** at end of session: `fbf9c1b` `312ff0e` `b8a3334` `cd1311a`.

> [!note] What next session should pick up
> If verification has cleared: [[CHECKLIST]] §1 → §2, in order, one report before the full set.
>
> If it hasn't: AWS Builder ID (five minutes, needs no AWS account), record [[VIDEO_SCRIPT]] §1/§2/§4, and the first builder.aws post. That bonus is worth up to +0.6 on a 5-point scale and the retrieval-failure story is already written up in three places.

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
| `src/provider.py` | `get_model(role)` — Haiku 4.5 / Sonnet 4.6 / Opus 4.6, prompt caching on all three. `--list` lists Bedrock profile ids (but see 2026-08-31: listing is not an entitlement check). |
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

- ~~Bedrock inference-profile ids unverified.~~ Verified 2026-08-31; the triage id was wrong and is fixed.
- ~~Bedrock **model access** must be granted in the console.~~ **No longer true** — that console page has been retired and serverless models auto-enable on first invocation. What does gate a new account: the Anthropic use-case form, and tier entitlement (Sonnet 5 / Opus 5 are denied). See the 2026-08-31 entry.

---

## 2026-08-12 — Branding and plan

- [[BRANDING]] settled: **Porchlight**, *your friendly neighborhood agent*. Amber-on-dusk palette, Concept B mark, eight rendered brand assets in `assets/branding/`.
- Trademark scope resolved — supersedes the internal contradiction in [[PROJECT_BRIEF]] §11, which bans "Spidey" and then offers it as safe four lines later.
- [[IMPLEMENTATION_PLAN]] approved: sequential workflow, Bedrock, ChromaDB local embeddings, CLI intake, static S3 dashboard.
- **Real deployment confirmed as a goal**, which pulled the safety architecture (§4) forward into this pass rather than leaving it to phase 2.
- Model split (Haiku/Sonnet/Opus 5) + prompt caching adopted: ~$0.90 per 38-report run instead of ~$2.20, so ~55 runs inside the $50 rather than ~20.

---

## 2026-08-31 — first live run

Bedrock credentials worked end to end for the first time. Three gates in
sequence, each one only visible after the previous cleared:

1. **AWS account verification.** `ConverseStream` returned `AccessDenied`
   ("your account is currently being verified"). Listing inference profiles is a
   read and succeeded throughout, which made this look like a model-id fault.
2. **Anthropic use-case form.** Bedrock's *Model access* console page has been
   retired — serverless models auto-enable on first invocation — but Anthropic
   models still require a one-time use-case submission per account.
3. **Tier entitlement.** Sonnet 5 and Opus 5 return `AccessDenied` on a new
   account. **A profile listing as `ACTIVE` is not an entitlement check**; only
   an invocation is. Available: Haiku 4.5, Sonnet 4.6, Sonnet 4.5, Opus 4.6,
   Opus 4.5. Denied: Sonnet 5, Opus 5, Opus 4.7, Opus 4.8, Fable 5.

**Defect found and fixed.** `DEFAULT_MODELS["triage"]` was
`global.anthropic.claude-haiku-4-5`, which does not resolve — Haiku 4.5 is
published only as a dated profile. Sonnet and Opus carry bare aliases; Haiku
does not. Anyone cloning the repo would have failed on report 1.

**Decision: run on Sonnet 4.6 + Opus 4.6** rather than spend the remaining two
weeks pursuing tier access. Docs updated to name the models that actually
produced the demo. Entries above naming Sonnet 5 / Opus 5 were true when
written and are left as they were.

### Full 38-report run — two of four behaviours pass

| Behaviour | Expected | Result |
|---|---|---|
| ~29 one-offs logged silently | 29 | **28** — the community-garden reports correlated and alerted |
| Near-miss declined (3 zones, 3 weeks) | decline | ❌ **alerted** |
| Single-reporter cluster declined (4 reports, 1 reporter) | decline | ✅ declined |
| Genuine cluster alerts exactly once | 1 alert | ✅ declined → alert → suppressed |

Three alerts fired where the design calls for one. The suppression logic works:
the parcel-locker cluster alerted on its third report and was suppressed on the
fourth, which is the behaviour `seed_reports.json` `_about.alert_window`
describes.

**The failure is calibration, not incoherence.** The escalation reasoning is
sound throughout — it correctly identifies thin baselines, distinguishes
corroboration from repeat-reporting by one person, and argues against alerting
on ordinary behaviour. But it is weighting `distinct_reporters` above the
anomaly score, and the anomaly score separates the cases cleanly:

    Birch Ln          false alert    z=0.9
    Community garden  false alert    z=1.4
    Parcel lockers    correct        z=6.5

That separation is the lever for §3 tuning. Note the prompts were written
against documented Opus 5 behaviour and have never been tuned for 4.6.

---

## 2026-08-31 → 09-01 — tuned, held, and made visible

Four things happened: the over-alerting was fixed, the fix held across two full
runs, the holdout was spent and passed, and the report page now shows the raw
reports beside what was stored.

### The escalation prompt was discounting the wrong direction

The prompt taught the model to distrust a *high* anomaly score built on a thin
baseline. It never said a *low* score was disqualifying. So the model wrote the
objection down and then argued past it — *"the anomaly score of 0.87 is not
high, but ... it doesn't carry much weight either way"* — and alerted twice on
quiet zones. Two edits to `ESCALATION`:

- the score now cuts both ways, with a sentence naming the exact move: *when you
  find yourself writing that the score is low but something else outweighs it,
  that is the moment to decline*
- spread counts inside a single zone too. The old text only covered spread
  *across* zones, which left a one-zone cluster over 29 days unaddressed.

Both false alerts now decline, in the prompt's own words: *"four reports in 30
days is about one a week, which describes what a shared community garden
normally looks like."*

### Two clean runs, and the wobble worth knowing about

| | run 3 | run 4 |
|---|---|---|
| alerts | **1** | **1** |
| near-miss / Birch Ln | declined | declined |
| community garden | declined | declined |
| single reporter (4 reports, 1 person) | declined | declined |
| 4th cluster report | suppressed | suppressed |
| silent / declined | 26 / 10 | 27 / 9 |

The alert fires both times at 3 reports · 3 reporters · 13h · z=6.5. The last
row is the honest caveat: one report moved between *silent* and *declined*
across runs. Neither is an alert, so nothing claimed is affected, but the tally
can shift by one. Do not quote 26/10 as if it were fixed.

### The holdout, spent

Run once on 2026-08-31 against the prompts as committed. **20 of 20.** Full
transcript in `data/holdout_result_2026-08-31.log`; the reasoning is in
[[README]] § *The holdout run*. Both adversarial cases landed — the
no-shared-vocabulary bike cluster was found, the four "parked car on Sycamore
Row" reports stayed quiet.

Two things recorded rather than rounded up. The alert fired on the **second**
report at z=2.1 rather than the third at z=6.5, because that zone had no
history at all and the agent said so before setting the number aside. And the
run produced **zero declines** — the Sycamore Row four never grouped, so
retrieval separated them rather than judgment refusing them. The holdout proves
the agent finds a hard cluster and resists a lexical trap. It does not prove it
can decline a plausible one.

### Three documented claims were wrong, and are now right

The three-behaviours table in [[README]] and [[DEVPOST]] said the alert fires on
4 reports / 4 reporters / 36 hours. It fires on the **third** report — 3
reporters, 13 hours. The 4/4/36h state belongs to the report that was
*suppressed*. README also carried `z = 5.0`, which matches neither the alert
(6.5) nor the final cluster (9.0).

Bigger: the near-miss row claimed the agent weighs three reports across three
zones and declines on the spread. **It does not.** Retrieval never links the
three to each other — 0.436–0.456 between them, against 0.576 from one of them
to an unrelated report. Two are logged silently with nothing correlated; the
third links to unrelated reports on its own street. None surfaces, which is the
outcome wanted, but not for the reason claimed. The "why an agent, not a
threshold" section overclaimed in the same way and now carries the coda.

### The report page shows its work

A two-column section: the message as it arrived, beside the normalized sentence
actually indexed. It makes both central claims visible without a paragraph of
explanation —

    "a guy hanging around the mailboxes"          → parcel lockers, bldg 3
    "loitering by the post boxes again tonight"   → parcel lockers, bldg 3
    "messing about near where the packages get    → parcel lockers, bldg 3
     dropped"
    "waiting around by the delivery lockers"      → parcel lockers, bldg 3

Four phrases, no shared content word. `raw_text` is opt-in at all three
boundaries (`rendered_rows(include_raw=)`, `render.write(show_raw=)`,
`--show-raw`), because a renderer that gets it by default is how the retention
guarantee becomes a leak — and it would leak silently, since the page renders
fine either way. Two tests hold the line.

### Infrastructure

- **Bedrock read timeouts abort a whole run.** Report 26 of 38 was lost to one.
  botocore defaults to 60s, and correlation makes tool calls then writes prose
  against a 16384-token ceiling. `read_timeout=300` with standard-mode retries.
  Not something to discover while recording, or on a one-shot holdout.
- **`--holdout` and `--seed`** added; the holdout had existed since 2026-08-14
  with no way to run it. It takes its own database and vector store, because the
  anomaly detector scores a zone against its own history and 38 seed reports
  left in the store would silently redefine "unusual".
- **Cost:** credits confirmed to cover Bedrock (checked the applicable-services
  list). $190 available across four credits, roughly $3–5 spent. Cost Explorer
  was enabled 2026-09-01 and had not ingested yet; `AWSBillingReadOnlyAccess` is
  attached to the `porchlight` IAM user, so the real per-service figure can be
  read directly from **2026-09-02** onward.

### Two mistakes worth recording

**The demo database was destroyed.** `--holdout` used `os.environ.setdefault`,
and `.env` ships `FNA_DB_PATH=porchlight.db`, so the flag deferred to the
ambient value and `fresh_state()` deleted the completed run on the way in. An
explicit flag has to win over ambient config. Recovered by re-running; the
rendered page and logs had survived.

**`⟨PENDING.md` is gone.** It was untracked at session start and is no longer on
disk. It was never committed, so git cannot recover it. Cause unknown — recreate
it if it mattered.

---

## 2026-09-02 — the page redesigned, and a checker so the numbers stop drifting

Nothing about the agent changed. This was a packaging session: the report page
was rebuilt around a stated product direction, and the figures scattered across
six surfaces were pulled back into agreement with the run.

### Four published numbers had drifted from the run they described

Found by reading the surfaces against the database rather than against each
other:

- [[VIDEO_SCRIPT]] quoted the alert as **4 reports / 4 reporters / 36 hours**.
  It fires at **3 / 3 / 13**; the 4/4/36 state belongs to the report that is
  *suppressed*.
- §1 paraphrased four seed reports — *"a person hanging around the mailboxes"*
  for the seed's *"a guy"*. Harmless until the redesigned page began showing the
  same four reports verbatim, at which point a judge would see one report worded
  two ways inside three minutes.
- [[IMPLEMENTATION_PLAN]] still carried the **$0.90/run** list-price estimate.
- The page header said *"one street, last night"* for a dataset spanning eight
  zones and thirty-seven days.

Every one of them was true when it was written, and none was caught by a person
re-reading the file. So `scripts/check_claims.py` now derives the truth from the
live database and checks each surface against it — the report page, [[README]],
[[DEVPOST]], [[VIDEO_SCRIPT]], [[IMPLEMENTATION_PLAN]] and
`assets/architecture.html`. It exits non-zero on drift, so it can gate a
recording session or a commit. It checks figures, the verbatim quotes that go on
camera, and the structural guarantees of the page. It does not check prose.

**The rule it encodes:** a number that appears on two surfaces can disagree with
itself, so either derive it from the run or check it against the run.

### The real cost, measured

**$9.39 of Bedrock spend across roughly 190 reports processed** — read from the
AWS credits page, not calculated from list prices. That is about **5 cents a
report, ~$1.90 per 38-report run** — roughly double the $0.90 estimate, which is
what the two corrections recorded on 2026-08-20 predicted. $182.95 of $190 in
credits remains; the DevPost $50 was never needed.

It is declared once, as `COST` in `src/render.py`, carrying its own source
string. Same for `HOLDOUT`, which carries its limit inline so the number cannot
be published without it.

### The page rebuilt around "what you heard / what happened"

Direction locked in [[PRODUCT]], written this session and approved: the page
splits the way the product does — one side the single message that reached a
neighbour, the other everything that was kept from them. The canvas went from
900×380 to 640×460, because it now sits beside the refusal rather than spanning
the page, and `NEAR` was lightened `#3A4A6B` → `#5C7098`.

One relaxation, decided deliberately: **a short inline script is now permitted.**
The self-contained rule holds — no CDN, no network request, one file — and
everything still degrades to a readable page with JavaScript off, because the
file is also screen-recorded.

### The video script caught up with the run

- **§3b no longer describes a decline that does not happen.** The old beat
  opened on the near-miss — *"three zones, three weeks, declined on the spread"*
  — and the agent never does that; retrieval never links those three to each
  other, so no cluster is ever assembled to refuse. Replaced with the
  single-reporter decline, which is the stronger beat anyway: a real, tight,
  plausible cluster that the agent says no to. The honest near-miss framing is
  kept as an optional ten seconds.
- **§3d added** — the two-column transcript, four phrasings collapsing to one
  stored sentence. The best visual in the project and the script had no mention
  of it. Its 25 seconds come out of §3b (one decline, not two) and §4 (trimmed
  60s → 50s), so the running time is unchanged.
- **The holdout moved into §5** as a fixed beat rather than an if-you-have-time
  extra, with its caveat written down beside it.

### Not done

`out/report.html` is regenerated and current, but it is still only on disk —
nothing is hosted, so [[DEVPOST]]'s live-demo field is still `⟨PENDING⟩`.

---

## 2026-09-09 — the backlog pushed

Housekeeping at the top of the final week. `main` had been **8 commits ahead of
`origin/main`** since 2026-09-01, and the whole 2026-09-02 session was
uncommitted on top of that — the redesigned renderer, [[PRODUCT]], the claims
checker and the rewritten script. The public repo is what a judge clones, and it
predated most of that work. Now pushed.

Two defects in the uncommitted script, fixed on the way past: a stray `/`
keystroke below the frontmatter, and a callout title split across two lines,
which Obsidian rendered as a nested blockquote rather than a title.

`.freeze/` (the frozen run-4 state, kept so the demo can be restored) and
`.impeccable/` (design-tool scratch and review screenshots) are now ignored.
Both are local safety nets, neither is source.

Verified before pushing: **55 tests passing, 13 skipped**, and
`scripts/check_claims.py` green on every figure — one warning, the four
unresolved `⟨PENDING⟩` placeholders in [[DEVPOST]].

---

## 2026-09-10 — the page is online

The live demo link exists. `out/report.html` — run 4, with the transcript
section — is at
**https://porchlight-report.s3.us-east-1.amazonaws.com/index.html**, confirmed
reachable with no credentials: HTTP 200, `text/html; charset=utf-8`, no offline
band. Also set as the repo's GitHub **homepage**, which puts it at the top of
the About sidebar for anyone who arrives at the source first.

That closes the cheapest Technical Implementation point available, and the
Devpost "Try it out" field. **One `⟨PENDING⟩` is left: the video URL.**

### Neither planned route worked, and the reason is worth keeping

[[CHECKLIST]] offered two ways to do this — install the AWS CLI and run
`publish.sh`, or click through the S3 console. Both assumed a permission that
was not there. The `porchlight` IAM user had `AmazonBedrockFullAccess` and
`AWSBillingReadOnlyAccess` and **no S3 access at all**; `list_buckets` returned
`AccessDenied`. It cannot grant itself, so this needed a console visit as the
account owner regardless. `AmazonS3FullAccess` was attached 2026-09-10.

The AWS CLI is still not installed, and does not need to be. `scripts/publish.py`
does what `publish.sh` does — bucket, public-access block, read policy, website
config, upload — through **boto3, which is already a dependency of the
pipeline**. `publish.sh` silently required a separate installation this project
otherwise never asks for, which is the kind of dependency a judge discovers only
when the publish step fails on them. Both scripts now exist; the shell one is
for anyone who prefers the CLI.

Two details that cost a retry each and are written into the script:

- **Clearing the public-access block is not instant.** A bucket policy applied
  immediately afterwards is refused, and the error reads as though the *policy*
  were wrong. Six attempts, three seconds apart.
- **`porchlight-demo` was taken.** Bucket names are globally unique across all
  of AWS, not per-account. `porchlight-report` was the fallback.

**The submission link is the HTTPS one.** S3's website endpoint is HTTP-only, and
a judge following an `http://` link can meet a browser warning before they meet
the project. The website endpoint works and is recorded, but nothing should be
submitted with it.

> [!warning] Re-publish if the page is ever re-rendered
> `python scripts/publish.py porchlight-report us-east-1`. The published page,
> the terminal footage and the video must not disagree — that is the whole
> premise of `scripts/check_claims.py`, and a stale upload defeats it silently.

> [!note] Detach `AmazonS3FullAccess` when the hackathon is over
> Nothing needs it once the page is up, and it is broader than one bucket
> warrants.

### Housekeeping

README got a prose pass — em dashes traded for commas, colons and parentheses
throughout. No figure moved; `check_claims.py` is green. `oldREADME.md`, a
20KB copy left in the repo root, is deleted: every committed version is in git
history, and a second README in a public repo is a thing that confuses a reader
who finds it.
