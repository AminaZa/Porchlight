---
tags: [checklist, hackathon, porchlight]
status: active
created: 2026-08-14
updated: 2026-08-31
---

# Checklist

> Everything still outstanding, in dependency order. Tick boxes directly in Obsidian.
> Companion to [[IMPLEMENTATION_PLAN]] (how) and [[PROGRESS]] (what happened).

> [!danger] Deadline: **Monday 14 September 2026, 5:00pm PT**
> Confirmed from the official rules — this was previously unknown and the brief's
> "six weeks from project start" was wrong. As of 2026-08-21 that is **24 days**.
> The AWS credits request form closes earlier, **11 September, 12pm PT**.

> [!success] AWS is wired — 2026-08-31
> Signup completed. IAM user created, `AmazonBedrockFullAccess` attached, access
> key written to `C:\Users\RAZER\.aws\credentials`. `--list` sees 25 Anthropic
> profiles in `us-east-1` and all three roles report **OK**.
>
> **The Bedrock "Model access" console page has been retired.** Serverless
> foundation models auto-enable on first invocation, so §1's "grant model access"
> step no longer exists as a thing you can click.
>
> **One real defect found and fixed:** `DEFAULT_MODELS["triage"]` was
> `global.anthropic.claude-haiku-4-5`, which does not resolve. Haiku 4.5 is only
> published as a dated profile — `global.anthropic.claude-haiku-4-5-20251001-v1:0`.
> Sonnet 5 and Opus 5 were correct unversioned. A judge cloning the repo would
> have hit this on report 1. Corrected in `src/provider.py` and `.env.example`.
>
> **Now blocked only on AWS account verification** — a clock, not a config.
> `ConverseStream` returns AccessDenied: *"Your account is currently being
> verified. Verification normally takes less than 2 hours."* Listing profiles is
> a read and already works; invocation is a spend operation and is gated. If it
> still fails after ~2 hours, write to aws-verification@amazon.com.

> [!note] Everything is pushed as of 2026-08-21
> `main` is level with `origin/main` — the guard, the defect fixes, the video
> script and the Devpost copy are all on GitHub.

---

## 1 · Unblock Bedrock

- [x] **AWS signup completes** ✅ 2026-08-31
- [x] Create an IAM user, attach `AmazonBedrockFullAccess`, create an access key
      (*Application running outside AWS*) ✅ 2026-08-31
- [x] Write it to `C:\Users\RAZER\.aws\credentials` under `[default]` — boto3
      reads this with no env vars and no CLI install ✅ 2026-08-31
- [x] ~~Grant Bedrock **model access** in the console~~ — **the page is retired**,
      models auto-enable on first invocation. Nothing to do
- [x] Check *which* region actually has all three — `us-east-1` carries all three,
      as both `global.` and `us.` profiles ✅ 2026-08-31
- [x] Run `python -m src.provider --list` and confirm all three report **OK**
      ✅ 2026-08-31
- [x] Paste the real profile ids into `.env` — triage needed the versioned id;
      all three now pinned in `.env` *and* corrected in `DEFAULT_MODELS`
- [x] **Wait out AWS account verification** ✅ 2026-08-31 — three sequential
      gates, each only visible once the previous cleared
- [x] Set an **AWS Budget with a zero-spend alert** ✅ — "My Zero-Spend Budget",
      $1 limit, `IncludeCredit: True` so it reports cost *after* credits
- [x] **Credits confirmed to cover Bedrock** ✅ 2026-09-01 — $190 across four
      credits, and "Amazon Bedrock" is in the applicable-services list. Spent
      roughly $3–5. `AWSBillingReadOnlyAccess` attached to the `porchlight` IAM
      user and Cost Explorer enabled 2026-09-01, so from **2026-09-02** the real
      per-service figure can be read directly
- [x] ~~**Request the $50 credits**~~ — form closes 11 Sep 12pm PT. **No longer
      load-bearing:** since Jul 2025 a new account gets **$100 on activation**
      plus up to $100 more for five onboarding tasks — one of which is testing a
      Bedrock prompt. Against a $20–50 project that is full coverage, so the
      hackathon credits are now a bonus, not a dependency. The Free Plan expires
      after six months or when credits run out; we need three weeks

---

## 2 · First real runs

- [x] **One report through the CLI** ✅ 2026-08-31 — and it earned its place:
      this is exactly where the Sonnet 5 entitlement problem surfaced, at the
      correlation stage, instead of on report 1 of 38. Ran clean on 4.6 and
      **declined correctly** (2 reports, 1 reporter, z=7.85 called out as an
      artifact of a thin baseline)
  ```
  python -m src.intake.cli "someone took my package from the porch" --zone "Elm St north"
  ```
- [x] **Full demo** ✅ — four live runs. Runs 3 and 4 both clean
- [x] Confirm all four designed behaviours actually happen ✅ **4 of 4, twice**
    - [x] one-offs logged silently — 26 or 27 depending on the run
    - [x] the near-miss produces **no alert** — but see the correction below: it
          is never correlated into one situation, so this is not the
          "declines on the spread" moment the video script assumed
    - [x] the single-reporter run **declined** (4 reports, 1 reporter)
    - [x] the parcel-locker cluster **alerts**, exactly once, on its 3rd report
          at z=6.5, with the 4th suppressed
- [x] `python -m pytest tests/` green ✅ **55 passing**, 13 skipped
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

## 2b · Models actually available — the docs must follow the code

> [!warning] This account cannot use Sonnet 5 or Opus 5 — resolved to 4.6 on 2026-08-31
> Probed every Anthropic profile in `us-east-1` by invoking each one directly.
> **`--list` shows a profile as ACTIVE whether or not the account is entitled to
> it**, so listing is not an entitlement check — only a real call is. That is why
> this surfaced at the correlation stage of the first run rather than at `--list`.
>
> | Model | This account |
> |---|---|
> | Haiku 4.5 | ✅ |
> | Sonnet 4.6 · Sonnet 4.5 · Opus 4.6 · Opus 4.5 | ✅ |
> | **Sonnet 5 · Opus 5** · Opus 4.7 · Opus 4.8 · Fable 5 | ❌ AccessDenied |
>
> A new AWS account does not get the newest tier, and the error points at AWS
> Sales — an enterprise process, not a form. **Decision 2026-08-31: run on
> Sonnet 4.6 + Opus 4.6** rather than spend the remaining days chasing access.
> `.env` now pins triage Haiku 4.5 · correlation Sonnet 4.6 · escalation Opus 4.6.

Every surface below still claims Sonnet 5 / Opus 5. The submission has to name
the models that actually produced the demo — a judge who reads the README and
then watches the video should see the same thing in both.

- [ ] `assets/architecture.html` — three places (~344, ~355, ~450). **Blocks
      video §4**, which is shot from this file, so do this one first
- [ ] `README.md` — the pipeline diagram (~36) and the cost paragraph (~134)
- [ ] `DEVPOST.md` — ~128, ~137, and the "Built with" list (~146)
- [ ] `IMPLEMENTATION_PLAN.md` — the model row (~31), the price table (~46–47),
      the tree diagram (~72, ~75). Per-token prices differ per model, so the
      per-run cost estimate needs recomputing against the measured figure
- [ ] `src/provider.py` — module docstring, `DEFAULT_MODELS`, and the three
      comment blocks that reason about Sonnet 5 / Opus 5 behaviour
- [ ] `PROGRESS.md` — **append, do not rewrite.** It is a log of what happened,
      and the Sonnet 5 / Opus 5 entries were true when they were written
- [ ] `src/prompts.py` — **not a find-and-replace.** The prompts were written
      against documented Opus 5 behaviour (*"writes long by default"*, *"verifies
      its own work unprompted"*, *"will otherwise widen a task"*). Whether those
      hold on Opus 4.6 is a §3 tuning question, not a rename
- [ ] Re-check the two §2 predictions against 4.6. Adaptive-thinking-by-default
      is an Opus 5 / Sonnet 5 behaviour, so on 4.6 `max_tokens` may not be eaten
      by thinking at all — which would make the run *cheaper* than the $1.20–1.50
      budgeted, not dearer. Likewise `MIN_CACHEABLE_TOKENS` was measured for the
      5-series and may differ

---

## 3 · Prompt tuning

> [!warning] The brief names this as a real schedule risk (§13), not a formality
> Budget genuine time. It is prompt engineering, not code, and it is where the
> demo goes from "runs" to "persuasive".

- [x] Tune until the four behaviours above are stable across repeated runs
      ✅ 2026-09-01. First live run scored 2 of 4; runs 3 and 4 both score 4 of
      4. Fixed by two edits to `ESCALATION` — a low anomaly score is now a
      reason to decline rather than a neutral fact, and spread counts inside a
      single zone as well as across zones. One caveat for anyone reading the
      tally: a report moved between *silent* and *declined* between runs 3 and
      4. Neither is an alert, but do not quote the split as fixed
- [ ] Re-check verbosity — this was written for Opus 5, which writes long by
      default. Re-measure on Opus 4.6 rather than assuming it inherits the trait.
      The alert message should stay 2–3 sentences
- [ ] Confirm alerts never contain a person description, even when the raw report
      had one — and that the new `RedactionGuard` isn't firing on ordinary reports
      (precision is asserted offline in `tests/test_guards.py`; live is the real test)
- [x] **The holdout — spent 2026-08-31. 20 of 20.** ✅ Transcript in
      `data/holdout_result_2026-08-31.log`, written up in [[README]] § *The
      holdout run* and [[DEVPOST]]
    - [x] the no-shared-vocabulary bike cluster is found — alerts once, rest suppressed
    - [x] the four same-street parked-car reports are **not** merged — all silent
    - [x] recorded with what it does **not** prove: zero declines, so the run
          never exercised the correlate-then-refuse path

> [!danger] The holdout is spent. Do not run it again
> Re-running it after any prompt change turns it back into tuning data and the
> number stops meaning anything. If a prompt has to change from here, the
> honest options are to say so beside the result or to author a second set.

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
- [x] **Bonus: builder.aws.com posts** — up to **+0.6** on a 5-point scale, 0.2 each,
      max three, published *before* the deadline. Use "Agents for Humans" in the title.
      **The platform caps a post at 3000 characters.** All three drafts were cut to
      fit on 2026-08-22; `python scripts/postlen.py` checks the pasteable body of
      each and exits non-zero if any is over
    - [x] Post 1 — **PUBLISHED 2026-08-22.** The retrieval failure: −0.16 separation,
          redaction turning out to be what *makes* retrieval work. URL is in the
          file's frontmatter. **+0.2 banked**
    - [x] Post 2 — **PUBLISHED 2026-08-22.** Why a similarity threshold can't do
          this: the ordering is inverted and the deciding evidence is metadata.
          **+0.2 banked.** URL recorded in the file's frontmatter
    - [x] Post 3 — **PUBLISHED 2026-08-22.** A prompt is not a control: the
          `AfterModelCallEvent` hook, why `event.retry` is the point, and the
          `toolUse` bug that made the guard a no-op. **+0.2 banked.** URL recorded in
          the file's frontmatter

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

---

## Next session — start here

> [!note] State as of 2026-09-01
> Working tree clean, `main` level with origin. 55 tests passing. The agent is
> **done being tuned** — runs 3 and 4 both score 4 of 4, and the holdout is
> spent at 20/20. Nothing below requires touching a prompt. **13 days left.**

Everything remaining is packaging. In the order it should be done:

### 1 · ~~Put the report page online~~ ✅ 2026-09-10

**https://porchlight-report.s3.us-east-1.amazonaws.com/index.html**

Run 4, with the two-column transcript. Confirmed reachable with no credentials
(HTTP 200, `text/html; charset=utf-8`, no offline band). Also set as the repo's
**homepage**, so it shows at the top of the GitHub About sidebar.

- [x] Published — **not** by either route planned here. The AWS CLI was never
      installed, and `porchlight` had no S3 permissions at all;
      `AmazonS3FullAccess` was attached 2026-09-10. `scripts/publish.py` does the
      same job through boto3, which is already a dependency, so nothing extra
      needs installing. `publish.sh` is kept for anyone who prefers the CLI
- [x] URL pasted into [[DEVPOST]]
- [ ] **Detach `AmazonS3FullAccess` after the hackathon.** Nothing needs it once
      the page is up, and it is broader than one bucket warrants
- [ ] If `out/report.html` is ever re-rendered, re-publish it:
      `python scripts/publish.py porchlight-report us-east-1`. The page and the
      video must not disagree

> [!note] `porchlight-demo` was taken
> Bucket names are globally unique across all of AWS, and that one belongs to
> another account. `porchlight-report` was the fallback.

### 2 · Record the video — the largest remaining job

> [!important] [[SHOOT_RUNBOOK]] has the commands and the shot order
> Written 2026-09-10 and checked against the code, not from memory.

§1 and §2 are already shot. Outstanding:

- [ ] **§4 (architecture)** — no longer blocked; the diagram names Sonnet 4.6 /
      Opus 4.6 and the redaction guard is on it. Trim from 1:00 to ~40s to make
      room for the holdout result
- [ ] **§3** and **§5**
- [ ] **The transcript section is new and the script does not mention it.** It is
      the strongest visual in the project — four phrasings with no shared word,
      collapsing to one place — and it belongs on camera. Decide where before
      recording, not during
- [ ] Under 5:00, public on YouTube or Vimeo, URL into [[DEVPOST]]

### 3 · Loose ends

- [ ] **Delete `refs/`** before submission — 52MB of third-party footage,
      gitignored but still on disk
- [ ] Live redaction tests — `FNA_LIVE_TESTS=1 python -m pytest tests/test_redaction.py -v`
      (13 skipped tests, ~12 Haiku calls, a fraction of a cent)
- [ ] Cache-read check — `FNA_TRACE=1`. **Triage will stay flat; that is
      expected**, its prefix is ~960 tokens against Haiku 4.5's 4096 minimum
- [ ] Real cost from Cost Explorer — **readable from 2026-09-02**, permission
      and ingestion both now in place. Replaces the list-price estimate in
      [[IMPLEMENTATION_PLAN]] §  (the $0.90/run figure was computed for
      Sonnet 5 / Opus 5 and the 4.6 pair costs more)
- [ ] Clean-clone setup verification
- [ ] Submit on Devpost — **14 Sep 2026, 5:00pm PT**

### 4 · Known, deliberate, not bugs

- **The near-miss never correlates.** Its three reports sit at 0.436–0.456
  similarity to each other, lower than one of them scores against an unrelated
  report (0.576). None of them alerts, which is the right outcome, but the agent
  never assembles them into one situation to refuse. [[README]] and [[DEVPOST]]
  both say so. **[[VIDEO_SCRIPT]] still describes it as the persuasive decline
  moment — that beat needs rewriting or cutting before §3 is recorded.**
- **The silent/declined split moves by one between runs.** Both mean no alert.
  Do not quote it as fixed.
- **`⟨PENDING.md` is gone.** Untracked at session start, no longer on disk,
  never committed so git cannot recover it. Cause unknown. Recreate if it
  mattered.
