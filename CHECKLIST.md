---
tags: [checklist, hackathon, porchlight]
status: active
created: 2026-08-14
---

# Checklist

> Everything still outstanding, in dependency order. Tick boxes directly in Obsidian.
> Companion to [[IMPLEMENTATION_PLAN]] (how) and [[PROGRESS]] (what happened).

> [!danger] The one thing blocking everything
> **AWS credentials are not configured.** Nothing below the first section can start until they are. Every remaining engineering task, the video, and the live demo link all sit behind it.
>
> You do **not** need the `aws` CLI for the first step — `python -m src.provider --list` runs on boto3, which is already installed. You need credentials in the environment or `~/.aws/credentials`. The `aws` CLI *is* needed later, for `scripts/publish.sh`.

---

## 1 · Unblock Bedrock

- [ ] Configure AWS credentials (env vars or `~/.aws/credentials`)
- [ ] Grant Bedrock **model access** in the console, in your region, for all three:
    - [ ] `claude-haiku-4-5` (triage)
    - [ ] `claude-sonnet-5` (correlation)
    - [ ] `claude-opus-5` (escalation)
- [ ] Run `python -m src.provider --list` and confirm all three report **OK**
- [ ] Paste the real profile ids into `.env` if they differ from the defaults
- [ ] Set an **AWS Budget with a zero-spend alert** — free, and the only thing that catches a runaway loop during tuning

---

## 2 · First real runs

- [ ] **One report through the CLI** — do this *before* the full set; it is where credential and model-id problems surface, and far easier to read there than on report 1 of 38
  ```
  python -m src.intake.cli "someone took my package from the porch" --zone "Elm St north"
  ```
- [ ] **Full demo** — `python demo/run_demo.py --explain`
- [ ] Confirm all four designed behaviours actually happen:
    - [ ] ~30 one-offs logged silently
    - [ ] the near-miss **declined** (3 zones, 3 weeks) — the most persuasive moment in the video
    - [ ] the single-reporter run **declined** (4 reports, 1 reporter)
    - [ ] the parcel-locker cluster **alerts**, exactly once
- [ ] `python -m pytest tests/` still green against real model output
- [ ] **Redaction tests** — `FNA_LIVE_TESTS=1 python -m pytest tests/test_redaction.py -v` (13 tests, ~12 Haiku calls, a fraction of a cent)
- [ ] Check cache reads are landing: `FNA_TRACE=1 python demo/run_demo.py` — correlation and escalation input token counts should drop sharply after report 1. **Triage will not drop, and that is expected** — its prefix is ~960 tokens against Haiku 4.5's 4096-token minimum, so it never caches. See `src/provider.py` → `MIN_CACHEABLE_TOKENS`

---

## 3 · Prompt tuning

> [!warning] The brief names this as a real schedule risk (§13), not a formality
> Budget genuine time. It is prompt engineering, not code, and it is where the demo goes from "runs" to "persuasive".

- [ ] Tune until the four behaviours above are stable across repeated runs
- [ ] Re-check verbosity — Opus 5 writes long by default; the alert message should stay 2–3 sentences
- [ ] Confirm alerts never contain a person description, even when the raw report had one
- [ ] **Then, once, at the very end: the holdout.** 20 reports in `data/holdout_reports.json`, never looked at during tuning. Record the result in the README **whatever it is**
    - [ ] the no-shared-vocabulary bike cluster is found
    - [ ] the four same-street parked-car reports are **not** merged into one situation

---

## 4 · Submission deliverables

Straight from [[PROJECT_BRIEF]] §10.

- [x] Public repo URL — https://github.com/AminaZa/Porchlight
- [x] MIT license **visible in the About section** (GitHub detects it; confirmed via API)
- [x] README
- [x] Architecture diagram — `assets/architecture.html`, corrected against the built system
- [ ] **Setup instructions verified from an actual clean clone** — fresh directory, fresh venv, `pip install -r requirements.txt`, run the demo. Written but never tested from scratch
- [ ] **AWS Builder ID** — required, and easy to forget until the last day
- [ ] **Text description for Devpost** — what it does, who it's for, how it works
- [ ] **Demo video, max 5 minutes**
- [ ] **Live demo link** — optional but scores higher: `./scripts/publish.sh <bucket>` after a real (non-offline) run
- [ ] **Bonus:** post on builder.aws.com tagged `#AgentsforHumans`, published *before* the deadline
- [ ] Submit on Devpost

### Video structure (brief §10)

- [ ] **0:00–0:45** the problem — a channel full of reports nobody can correlate
- [ ] **0:45–1:15** who it's for — the volunteer coordinator
- [ ] **1:15–3:30** the working demo — one-offs logged silently, the near-miss **declined**, the real cluster alerting with reasoning visible
- [ ] **3:30–4:30** architecture — three agents, two correlation signals
- [ ] **4:30–5:00** why it matters, close

> [!important] Two things that will bite during recording
> **Never record `--offline`.** The escalation judgment there is a hard-coded rule. The banner, the page band and `publish.sh` all refuse it, but the camera won't.
>
> **The near-miss is the 20 seconds that sell it** (brief §10). Build the demo section around it — and note it is the one thing offline mode structurally cannot show, so it needs a real run.

---

## 5 · Open decisions

- [ ] **Confirm the actual Devpost deadline.** The brief says "6 weeks from project start" with no date written anywhere. Every schedule judgment below depends on it and nobody has looked it up
- [ ] **Alert recipient** — single block captain vs channel broadcast. Currently modelled as `EscalationDecision.audience`, so deciding late costs nothing
- [ ] **AgentCore / Lambda deployment** — brief §12 calls it a week-5 stretch, not a requirement
- [ ] **Discord intake** — brief §12 week-5 stretch. The CLI is what the pipeline is built on

---

## 6 · Optional, off the critical path

- [ ] `data/baseline_params.json` — calibrate the per-zone baselines against a real public dataset (NYC 311 or similar). Ship derived aggregates only, never rows. Lets the README say baselines are calibrated rather than hand-tuned
- [ ] Export the Porchlight mark as real SVGs — `assets/logo.svg` and a simplified `assets/logo-16.svg` ([[BRANDING]] flags that one scaled file turns to mud at favicon size)
- [ ] Favicon from the 16px variant

---

## Done

- [x] Branding settled — [[BRANDING]], eight rendered assets, trademark scope resolved
- [x] Implementation plan approved and kept current — [[IMPLEMENTATION_PLAN]]
- [x] Full vertical slice: models, provider, prompts, three agents, four tool modules, pipeline, renderer, CLI, demo runner
- [x] 38-report seed set, composition verified, premise proven at the data level (zero words shared across the four cluster reports)
- [x] 20-report holdout, written **before** tuning began
- [x] Offline demo mode — runs with no AWS account, labelled on every surface
- [x] 20 tests passing offline + 13 redaction tests waiting on credentials
- [x] Repo public, MIT, pushed, correct authorship, `main` branch
- [x] Architecture diagram corrected against the code
