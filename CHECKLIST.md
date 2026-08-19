---
tags: [checklist, hackathon, porchlight]
status: active
created: 2026-08-14
updated: 2026-08-20
---

# Checklist

> Everything still outstanding, in dependency order. Tick boxes directly in Obsidian.
> Companion to [[IMPLEMENTATION_PLAN]] (how) and [[PROGRESS]] (what happened).

> [!danger] Deadline: **Monday 14 September 2026, 5:00pm PT**
> Confirmed from the official rules — this was previously unknown and the brief's
> "six weeks from project start" was wrong. As of 2026-08-20 that is **25 days**.
> The AWS credits request form closes earlier, **11 September, 12pm PT**.

> [!warning] Currently blocked on AWS account verification (~72h, to about 23 Aug)
> Everything in §1–§3 sits behind it. Nothing in §4 or §5 does — that is where
> the next session's time should go if verification hasn't cleared.
>
> Credits are **not critical**. They cover build costs; without them the whole
> remaining project is roughly $20–50 of Bedrock usage out of pocket. Do not
> reshape the submission around them.

> [!note] 4 commits unpushed as of 2026-08-20
> `fbf9c1b` `312ff0e` `b8a3334` `cd1311a` — the guard, the defect fixes, the
> video script, the Devpost copy. Push when ready; nothing is on GitHub yet.

---

## 1 · Unblock Bedrock

- [ ] **AWS account verification clears** (~23 Aug)
- [ ] Create an IAM user, attach `AmazonBedrockFullAccess`, create an access key
      (*Application running outside AWS*)
- [ ] Write it to `C:\Users\RAZER\.aws\credentials` under `[default]` — boto3
      reads this with no env vars and no CLI install. **Never paste keys into chat**
- [ ] Grant Bedrock **model access** in the console, in one region, for all three.
      Console-only — no API, no script can do it:
    - [ ] `claude-haiku-4-5` (triage)
    - [ ] `claude-sonnet-5` (correlation)
    - [ ] `claude-opus-5` (escalation)
- [ ] Check *which* region actually has all three before committing — availability
      differs. Set `AWS_REGION` in `.env` to match (code now defaults `us-east-1`)
- [ ] Run `python -m src.provider --list` and confirm all three report **OK**
- [ ] Paste the real profile ids into `.env` if they differ from the defaults
- [ ] Set an **AWS Budget with a zero-spend alert** — free, and the only thing
      that catches a runaway loop during tuning
- [ ] **Request the $50 credits** — form closes 11 Sep 12pm PT

---

## 2 · First real runs

- [ ] **One report through the CLI** — do this *before* the full set; it is where
      credential and model-id problems surface, and far easier to read there than
      on report 1 of 38
  ```
  python -m src.intake.cli "someone took my package from the porch" --zone "Elm St north"
  ```
- [ ] **Full demo** — `python demo/run_demo.py --explain`
- [ ] Confirm all four designed behaviours actually happen:
    - [ ] ~30 one-offs logged silently
    - [ ] the near-miss **declined** (3 zones, 3 weeks) — the most persuasive moment in the video
    - [ ] the single-reporter run **declined** (4 reports, 1 reporter)
    - [ ] the parcel-locker cluster **alerts**, exactly once
- [ ] `python -m pytest tests/` still green against real model output (52 offline)
- [ ] **Redaction tests** — `FNA_LIVE_TESTS=1 python -m pytest tests/test_redaction.py -v`
      (13 tests, ~12 Haiku calls, a fraction of a cent)
- [ ] Check cache reads are landing: `FNA_TRACE=1 python demo/run_demo.py` —
      correlation and escalation input token counts should drop sharply after
      report 1. **Triage will not drop, and that is expected** — its prefix is
      ~960 tokens against Haiku 4.5's 4096-token minimum, so it never caches.
      See `src/provider.py` → `MIN_CACHEABLE_TOKENS`

> [!important] Two predictions to test on the first live run
> Neither has been observed — nothing has ever run against a real model.
>
> **`max_tokens` and adaptive thinking.** On Sonnet 5 and Opus 5, omitting the
> `thinking` parameter runs adaptive thinking, and `max_tokens` caps thinking plus
> response together. Raised 4096 → 16384 for both stages on 2026-08-20. If the
> stage still raises *"returned no structured output"* intermittently, that is
> the cause and the ceiling needs to go higher.
>
> **Per-run cost.** [[IMPLEMENTATION_PLAN]] §2 says ~$0.90; that predates both the
> triage cache finding and thinking-on-by-default. Budget ~$1.20–1.50 and measure
> it on run one. If it comes in high, `effort` is the lever — escalation at
> `medium` is worth testing on quality grounds anyway.

---

## 3 · Prompt tuning

> [!warning] The brief names this as a real schedule risk (§13), not a formality
> Budget genuine time. It is prompt engineering, not code, and it is where the
> demo goes from "runs" to "persuasive".

- [ ] Tune until the four behaviours above are stable across repeated runs
- [ ] Re-check verbosity — Opus 5 writes long by default; the alert message should
      stay 2–3 sentences
- [ ] Confirm alerts never contain a person description, even when the raw report
      had one — and that the new `RedactionGuard` isn't firing on ordinary reports
      (precision is asserted offline in `tests/test_guards.py`; live is the real test)
- [ ] **Then, once, at the very end: the holdout.** 20 reports in
      `data/holdout_reports.json`, never looked at during tuning. Record the result
      in the README **and in [[DEVPOST]]** whatever it is
    - [ ] the no-shared-vocabulary bike cluster is found
    - [ ] the four same-street parked-car reports are **not** merged into one situation

---

## 4 · Submission deliverables

Straight from [[PROJECT_BRIEF]] §10, cross-checked against the official rules.

**Done**

- [x] Public repo URL — https://github.com/AminaZa/Porchlight
- [x] MIT license **visible in the About section** (GitHub detects it; confirmed via API)
- [x] README
- [x] Architecture diagram — `assets/architecture.html`, corrected against the built system
- [x] **Video script drafted** — [[VIDEO_SCRIPT]], beat sheet + narration
- [x] **Devpost text description drafted** — [[DEVPOST]], 3 items marked `⟨PENDING⟩`

**Not blocked by AWS — do these during the verification wait**

- [ ] **AWS Builder ID** — required field, free, *separate from the AWS account and
      needs no verification*. Five minutes. Easy to forget until the last day
- [ ] Record [[VIDEO_SCRIPT]] §1, §2 and §4 — the problem, the audience, and the
      architecture walkthrough need no live run. That is ~2 of the 5 minutes
- [ ] **Bonus: builder.aws.com posts** — up to **+0.6** on a 5-point scale, 0.2 each,
      max three, published *before* the deadline. Use "Agents for Humans" in the title
    - [ ] Post 1 — the retrieval failure: premise check failing on the first run,
          −0.16 separation, and redaction turning out to be what *makes* retrieval work
    - [ ] Post 2 — why a similarity threshold can't do this (the sweep)
    - [ ] Post 3 — enforcing a safety guarantee with a Strands hook rather than a prompt

> [!note] The hashtag requirement was removed
> Rules updated 2026-08-12: `#AgentsforHumans` is **no longer required**. The title
> should still use the phrase *"Agents for Humans"*. [[PROJECT_BRIEF]] §10 still says
> otherwise and is out of date.

**Blocked on a real run**

- [ ] **Setup instructions verified from an actual clean clone** — fresh directory,
      fresh venv, `pip install -r requirements.txt`, run the demo. Written but never
      tested from scratch. *(`.env` loading was broken until 2026-08-20 — this check
      would have caught it)*
- [ ] **Demo video, max 5 minutes**, public on YouTube or Vimeo — [[VIDEO_SCRIPT]] §3
      needs live footage
- [ ] **Live demo link** — optional but scores higher: `./scripts/publish.sh <bucket>`
      after a real (non-offline) run
- [ ] Resolve the three `⟨PENDING⟩` items in [[DEVPOST]]
- [ ] Push the 4 local commits
- [ ] Submit on Devpost

> [!important] Two things that will bite during recording
> **Never record `--offline`.** The escalation judgment there is a hard-coded rule.
> The banner, the page band and `publish.sh` all refuse it, but the camera won't.
>
> **The near-miss is the 20 seconds that sell it** (brief §10). It is also the one
> thing offline mode structurally cannot show, so it needs a real run.

---

## 5 · Open decisions

- [x] ~~Confirm the actual Devpost deadline~~ — **14 Sep 2026, 5pm PT**. Resolved 2026-08-20
- [ ] **Alert recipient** — single block captain vs channel broadcast. Currently
      modelled as `EscalationDecision.audience`, so deciding late costs nothing
- [ ] **AgentCore / Lambda deployment** — brief §12 calls it a week-5 stretch, not a
      requirement. On 25 days, with the video unshot, this is the first thing to cut
- [ ] **Discord intake** — brief §12 week-5 stretch. The CLI is what the pipeline is
      built on

---

## 6 · Optional, off the critical path

- [ ] `data/baseline_params.json` — calibrate the per-zone baselines against a real
      public dataset (NYC 311 or similar). Ship derived aggregates only, never rows.
      Lets the README say baselines are calibrated rather than hand-tuned
- [ ] Export the Porchlight mark as real SVGs — `assets/logo.svg` and a simplified
      `assets/logo-16.svg` ([[BRANDING]] flags that one scaled file turns to mud at
      favicon size)
- [ ] Favicon from the 16px variant

---

## Done

- [x] Branding settled — [[BRANDING]], eight rendered assets, trademark scope resolved
- [x] Implementation plan approved and kept current — [[IMPLEMENTATION_PLAN]]
- [x] Full vertical slice: models, provider, prompts, three agents, four tool modules,
      pipeline, renderer, CLI, demo runner
- [x] 38-report seed set, composition verified, premise proven at the data level
      (zero words shared across the four cluster reports)
- [x] 20-report holdout, written **before** tuning began
- [x] Offline demo mode — runs with no AWS account, labelled on every surface
- [x] Repo public, MIT, pushed, correct authorship, `main` branch
- [x] Architecture diagram corrected against the code
- [x] **Redaction enforced structurally** — `src/guards.py`, a Strands hook on
      `AfterModelCallEvent` that retries on a leak and fails closed. 32 new tests
- [x] **Five defects fixed** — `.env` never loaded · telemetry documented but absent ·
      region mismatch · dead `write_log` · demo crashing on piped output on Windows
- [x] **52 tests passing offline** (was 20), + 13 redaction tests waiting on credentials
- [x] Hackathon paperwork kept local and gitignored — `REQUIREMENTS.md` is Devpost's
      and AWS's own text, not ours to redistribute
