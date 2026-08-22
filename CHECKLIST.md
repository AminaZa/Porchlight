---
tags: [checklist, hackathon, porchlight]
status: active
created: 2026-08-14
updated: 2026-08-21
---

# Checklist

> Everything still outstanding, in dependency order. Tick boxes directly in Obsidian.
> Companion to [[IMPLEMENTATION_PLAN]] (how) and [[PROGRESS]] (what happened).

> [!danger] Deadline: **Monday 14 September 2026, 5:00pm PT**
> Confirmed from the official rules — this was previously unknown and the brief's
> "six weeks from project start" was wrong. As of 2026-08-21 that is **24 days**.
> The AWS credits request form closes earlier, **11 September, 12pm PT**.

> [!warning] Blocked on AWS **signup**, not on verification — corrected 2026-08-21
> The account never finished registering. It is stuck at **step 4 of 5, phone
> verification**, failing with a generic "error processing your request".
>
> **Diagnosed cause: a country mismatch.** The card is Malaysian (Maybank) and
> was accepted at step 3; the phone is Tunisian (+216) and the IP is Tunisian.
> AWS's fraud screen compares those three and flags the disagreement. Nothing is
> wrong with the card.
>
> Fix path, in order: retry on a Malaysian `+60` number (voice call, not SMS) ·
> check the step-2 address matches the card's registered Malaysian address ·
> **open an Account activation support case** at aws.amazon.com/contact-us,
> naming the mismatch explicitly. Filed in parallel, not after the retries.
> Note the step rate-limits after repeated failures — retries stop working for
> a few hours regardless of what has been fixed.
>
> Everything in §1–§3 sits behind this. Nothing in §4 or §5 does.

> [!note] Everything is pushed as of 2026-08-21
> `main` is level with `origin/main` — the guard, the defect fixes, the video
> script and the Devpost copy are all on GitHub.

---

## 1 · Unblock Bedrock

- [ ] **AWS signup completes** — blocked at step 4 of 5, see the callout above.
      Support case is the reliable path; the SIM swap is the fast one
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
- [ ] **Request the $50 credits** — form closes 11 Sep 12pm PT. **No longer
      load-bearing:** since Jul 2025 a new account gets **$100 on activation**
      plus up to $100 more for five onboarding tasks — one of which is testing a
      Bedrock prompt. Against a $20–50 project that is full coverage, so the
      hackathon credits are now a bonus, not a dependency. The Free Plan expires
      after six months or when credits run out; we need three weeks

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
- [x] Architecture diagram — `assets/architecture.html`. **Refreshed 2026-08-21:**
      it predated `src/guards.py` (diagram 14 Aug, guard 20 Aug) and did not show the
      `RedactionGuard` at all. Added the guard band spanning triage→escalation, a
      fourth info card, and corrected the alert box now that `audience` is not a
      model choice
- [x] **Video script drafted** — [[VIDEO_SCRIPT]], beat sheet + narration
- [x] **Devpost text description drafted** — [[DEVPOST]], 3 items marked `⟨PENDING⟩`

**Not blocked by AWS — do these during the verification wait**

- [x] **AWS Builder ID** — created 2026-08-21. The Devpost field still needs the
      actual ID pasted in; see the `⟨PENDING⟩` in [[DEVPOST]]
- [ ] Record [[VIDEO_SCRIPT]] §4 — **§1 and §2 are shot as of 2026-08-21**, about
      1:15 of the 5:00 in the can. Only the architecture walkthrough is left of the
      no-live-run material; it can work from `assets/architecture.html`
- [ ] **Bonus: builder.aws.com posts** — up to **+0.6** on a 5-point scale, 0.2 each,
      max three, published *before* the deadline. Use "Agents for Humans" in the title
    - [x] Post 1 — **PUBLISHED 2026-08-21.** Draft in `posts/builder-post-1.md` (~950 words).
          The retrieval failure: premise check failing on the first run, −0.16
          separation, redaction turning out to be what *makes* retrieval work.
          Still unticked because the bonus requires it **published**, not written
    - [x] Post 2 — **PUBLISHED 2026-08-21.** Draft in `posts/builder-post-2.md` (~800 words).
          Why a similarity threshold can't do this: the ordering is inverted, the
          sweep is 10:1 against at every setting, and the deciding evidence is
          metadata. Carries one `⟨PENDING⟩` — the back-link to post 1's URL
    - [ ] Post 3 — **drafted 2026-08-21** in `posts/builder-post-3.md` (~1030 words).
          A prompt is not a control: the `AfterModelCallEvent` hook, why `event.retry`
          is the point, the `toolUse`-block bug that made the guard a no-op, and the
          precision-over-recall argument. All three posts now drafted and unpublished

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
      needs live footage. Motion direction for §1 and §2 is in [[MOTION_REFS]]
- [ ] **Delete `refs/` before submission** — 52MB of third-party reference clips
      plus `refs/_to_delete/` scratch frames. Now gitignored, but they still sit in
      the working tree. [[MOTION_REFS]] assumed this item already existed; it did not
- [ ] **Live demo link** — optional but scores higher: `./scripts/publish.sh <bucket>`
      after a real (non-offline) run
- [ ] Resolve the three `⟨PENDING⟩` items in [[DEVPOST]]
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
- [x] ~~**Alert recipient**~~ — **broadcast to the residents of the affected zone.**
      Resolved 2026-08-21. `Audience` collapsed to a single value `zone_residents`,
      so the agent no longer picks a recipient — widening the blast radius is a code
      change someone reviews, not a token a model emits. `ESCALATION` now tells the
      model the message is read zone-wide, that the reported person is likely among
      the readers, and bans anything that reads as *confront / follow / record /
      identify*. Human approval (`FNA_REQUIRE_APPROVAL`) matters more now, not less —
      the block captain used to be a second human check and broadcasting removes it
- [ ] **AgentCore / Lambda deployment** — brief §12 calls it a week-5 stretch, not a
      requirement. On 24 days, with the video unshot, this is the first thing to cut
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
