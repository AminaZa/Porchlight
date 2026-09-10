---
tags: [video, shoot, hackathon, porchlight]
status: active
created: 2026-09-10
---

# Shoot runbook — §3

> The operational companion to [[VIDEO_SCRIPT]]. That file is *what to say*;
> this one is *what to type, where, and in what order*. Read both before you
> start recording.

---

## 0 · The thing that decides everything

**`run_demo.py` deletes the database and starts from nothing.** `fresh_state()`
unlinks `porchlight.db` and resets the vector store on every run without
`--keep`. So the run you shoot is a *new* run, and it replaces run 4 — the run
that [[README]], [[DEVPOST]], `out/report.html` and the published S3 page all
currently describe.

That is the honest way to do it. It just has an "after" (§6 below), and skipping
it leaves the video and the live demo link describing different runs.

> [!success] The risk is smaller than it sounds
> Runs 3 and 4 both alerted at **3 reports · 3 reporters · 13h · z=6.5**, one
> alert, 38 in. Those are the only figures the script reads aloud. The one
> number known to move between runs is the **silent / declined split**, and
> [[VIDEO_SCRIPT]] §3a already forbids saying it out loud for exactly this
> reason. If run 5 matches, §6 is a five-minute confirmation. If it does not,
> `scripts/check_claims.py` names every line that needs changing.

> [!danger] Back up run 4 before you touch anything
> `.freeze/run4-backup/` already holds run 4's database, vector store, rendered
> page and alert log. Confirm it is there before the first take. If the shoot
> goes wrong you can restore it and be exactly where you are now.

---

## 1 · Where you are

**Working directory: the project root**, `C:\Projects\friendly\friendly-neigh-agent`.
Every command below runs from there, nowhere else. `run_demo.py` resolves its own
paths from the file location, but `.env` is only found from the root.

**Terminal:** Windows Terminal, dark background, per [[BRANDING]]. Not the default
`cmd.exe` window — the box-drawing characters and the `▲` marker need a UTF-8
console. `run_demo.py` reconfigures stdout to UTF-8 itself, so this works, but a
dark, large-font Windows Terminal is what the palette was designed against.

**Python:** use the venv explicitly so there is no ambiguity on camera:

```
.venv\Scripts\python.exe demo/run_demo.py --explain --html --show-raw
```

Plain `python` works too if the venv is activated. Pick one before you record and
do not switch mid-shoot.

---

## 2 · Before the first take

- [ ] `.freeze/run4-backup/` exists
- [ ] Terminal font large enough to survive YouTube compression. **Test at 1080p
      before committing to a take** — not after
- [ ] Window sized so a report line does not wrap. The lines run ~60 characters
      (`[01/38]  Parcel lockers, bldg 3     theft       ·  silent log`); a wrap
      turns the scroll into mush
- [ ] `FNA_TRACE` unset. With it set the run prints OpenTelemetry spans and the
      output is unusable
- [ ] `FNA_REQUIRE_APPROVAL` — know which way it is set before you run, so an
      approval prompt does not surprise you mid-take
- [ ] Notifications off, second monitor clear, clock hidden if it is in frame

### OBS

- **Window Capture on the terminal**, not Display Capture. No taskbar, no
  notifications, no second monitor creeping into frame
- **Record to MKV, not MP4.** If OBS crashes or the machine drops power
  mid-run, an MP4 is unrecoverable and an MKV is fine. Remux afterwards with
  File → Remux Recordings. This matters here more than usual: the run is long,
  single-take, and happens over a database you have just deleted
- 1920×1080, 30fps is plenty for a terminal. Push the bitrate up — text
  compresses badly and thin glyphs are the first thing to smear
- **No microphone.** Record the screen silent and do the voiceover separately.
  Narrating live means a fluffed line costs another full run: $1.90 and
  twenty-odd minutes. Silent footage can carry as many narration takes as you
  like
- **One take.** Start before you press enter, keep rolling through the whole
  run and through scrolling back up into the reasoning block. Cut it up in the
  edit — you cannot re-enter phase 3 later without re-running

### The approval prompt — turn it on

`.env` currently has `FNA_REQUIRE_APPROVAL=` (empty, so off). **Set it to `1`
for the shoot.**

`send_alert` is only reached in the alert branch — suppressed reports skip it —
so this fires **exactly once** in a 38-report run, at the alert:

```
  An alert is ready to send:
    ▲ Pattern — Parcel lockers, bldg 3
    <the message>
    cluster 3 · 3 reporters · 13h · z=6.5 · to Parcel lockers, bldg 3 residents

  Send it? [y/N]
```

That is the human-in-the-loop control [[PRODUCT]] calls the only check left now
that alerts broadcast zone-wide, and the hackathon theme is *"surfaces only when
a human decision is genuinely needed"*. It is that moment, on camera, for no
cost in scroll noise.

> [!danger] Answer `y`
> `src/pipeline.py` marks the cluster as alerted **only `if sent`**. Answer `N`
> and the fourth report is never marked covered, so the suppression beat in §3c
> does not happen and the tally changes. Answering `y` behaves identically to
> having the flag off.

> [!note] The code comment explaining why it is off is wrong
> `alerts.requires_approval()` says it is off "so a 38-report run isn't 38
> prompts". It would be one prompt, not 38 — dispatch is only called for alerts.

---

## 3 · The commands

### The only one you actually record

```
.venv\Scripts\python.exe demo/run_demo.py --explain --html --show-raw
```

One command does all three jobs:

| flag | what it does | why it is here |
|---|---|---|
| `--explain` | prints the `Why it decided what it decided` block after the run | §3b and §3c are shot from this block |
| `--html` | writes `out/report.html` | §3d, and the live demo link |
| `--show-raw` | puts the reporters' own words in the transcript | **§3d does not exist without it** |

> [!danger] Never record `--offline`
> The escalation judgment there is a hard-coded rule, not a model. The banner,
> the page band and both publish scripts refuse it. The camera will not.

> [!warning] Do not add `--holdout`
> The holdout was spent on 2026-08-31 and must not be run again — a second run
> after any prompt change turns it into tuning data and 20/20 stops meaning
> anything. It also uses its own database, so it would not show what you want.

### What the run costs, and how long to allow

About **$1.90** in Bedrock spend (5 cents a report, measured).

**Allow 10–25 minutes.** Measured 2026-09-10: one report cold, through
`src.intake.cli`, took **35 seconds** — and that includes the one-off cost of
importing, starting Chroma and loading the ONNX embedding model. Steady-state
per report is well under that, but correlation gets slower as the corpus grows,
because there is more to search and more to weigh. Do not plan around a
thirty-second run.

`read_timeout` is 300s with retries, so a long pause on one report is the system
working, not a hang.

> [!tip] Smoke-test first, on a throwaway database
> Verifies credentials, all three model ids, structured-output parsing,
> persistence and indexing for about five cents, without touching run 4. If
> something is misconfigured you find out here rather than on report 1 of 38
> with the camera rolling and the database already deleted.
>
> ```
> set FNA_DB_PATH=%TEMP%\smoke.db
> set FNA_CHROMA_PATH=%TEMP%\chroma-smoke
> .venv\Scripts\python.exe -m src.intake.cli "someone took my package from the porch" --zone "Elm St north"
> ```
>
> Then **open a new terminal** for the real run, so those variables are gone.
> Passed 2026-09-10: declined correctly, with reasoning.

Record the whole thing. Speed it up in the edit; §3a only needs thirty seconds of
screen time out of it.

### Commands you run *after*, not on camera

```
.venv\Scripts\python.exe scripts/check_claims.py
.venv\Scripts\python.exe scripts/publish.py porchlight-report us-east-1
```

---

## 4 · What the terminal actually shows

The output has three phases, and **the reasoning is not inline**:

```
  Porchlight — 38 reports

  [01/38]  Sycamore Row             other       ·  silent log
  [02/38]  Elm St north             hazard      ·  silent log
  ...                                                       <- phase 1: the scroll

  ▲ Pattern — Parcel lockers, bldg 3
  <the alert message, 2-3 sentences>
  cluster 3 · 3 reporters · 13h · z=6.5 · to Parcel lockers, bldg 3 residents

  [NN/38]  Parcel lockers, bldg 3   theft       ▲  ALERT     <- phase 2: fires mid-scroll
  ...
  [NN/38]  Parcel lockers, bldg 3   theft       ·  logged (cluster already alerted)

  ──────────────────────────────────────────────────────────
    Why it decided what it decided                           <- phase 3: at the very end
  ──────────────────────────────────────────────────────────

    Maple & 3rd  —  DECLINED
      <summary>
      evidence: 4 reports · 1 reporters · 85h · 1 zone(s) · z=2.2
      correlation: <the correlation agent's reading>
      decision:    <the escalation agent's refusal, in full>
```

**This changes the shot order.** You cannot pause on the decline as it happens,
because nothing is printed about it as it happens. §3a is phase 1. §3c's *alert*
is phase 2. §3b's and §3c's *reasoning* are both in phase 3, at the bottom, and
you get there by scrolling back after the run finishes.

---

## 5 · Shot by shot

### 3a · The quiet — 30s of screen time

**Shot:** the scroll, phase 1. Start recording before you press enter so the
first line is not clipped.

Let it run. Do not narrate over all of it — the script gives ~55 words for 30
seconds, which is slow on purpose. Silence while reports scroll reads as
confidence.

**In the edit:** speed-ramp the middle. Real time at the top so the format is
legible, fast through the middle, back to real time as the `▲ Pattern` block
approaches.

**Say `37 of 38`. Never read the split aloud.**

### 3b · The decline — hold, do not move

**Shot:** phase 3, the `Maple & 3rd — DECLINED` block. Scroll to it and stop.
Nothing moves for the whole beat.

The `evidence:` line is the proof and the `decision:` line is the argument. Let
both sit on screen long enough to actually be read — longer than feels
comfortable while you are the one who already knows what it says.

**One decline only.** There is one. Adding a second is padding.

If the terminal will not read at 1080p, the pickup is `out/report.html` under
*"And the one it refused."* — the same refusal, set in type. Use one or the
other, never both.

### 3c · The alert — two shots, from two phases

1. **The fire:** phase 2, the `▲ Pattern` block and the `▲ ALERT` line.
2. **The suppression:** a few lines later, the fourth report of the same cluster
   arriving as `· logged (cluster already alerted)`.
3. **The reasoning:** back to phase 3 for the escalation agent's words, if you
   want them.

**Read the numbers off the terminal on the day.** They were 3 / 3 / 13h / z=6.5
on runs 3 and 4 — but read what is on your screen, not what is written here.

### 3d · What it kept — the browser

**Shot:** open `out/report.html` and scroll to *"What was said, and what was
stored"*.

That section has a **Replay** button. It re-runs the reveal without reloading, so
you can take it as many times as you like. Use it.

Six rows, not four. The right column is four *different* sentences sharing one
place. **Say "the same place", never "the same sentence"** — see [[VIDEO_SCRIPT]]
§3d.

---

## 6 · After the shoot — the run you shot is now the run of record

Do this before you edit, not after.

1. **Re-check every published figure against the new run:**
   ```
   .venv\Scripts\python.exe scripts/check_claims.py
   ```
   Green means run 5 said what run 4 said and nothing needs changing. Any `FAIL`
   line names the file and the figure. Fix those first — they are the difference
   between a judge reading a number and a judge catching you out.

2. **Re-publish the page**, or the live demo link describes a run the video does
   not show:
   ```
   .venv\Scripts\python.exe scripts/publish.py porchlight-report us-east-1
   ```

3. **Re-run the tests:** `.venv\Scripts\python.exe -m pytest tests/ -q`

4. **Commit** the regenerated state and any figure corrections.

> [!important] The order matters
> Check first, publish second. Publishing a page whose numbers you have not
> checked is how the S3 link and the video end up disagreeing in public.

---

## 7 · If it goes wrong mid-run

- **A stage raises "returned no structured output"** — `max_tokens` too low for
  thinking plus response. It is 16384. Re-run; if it repeats, raise it.
- **A read timeout** — `read_timeout=300` with retries is already set. Report 26
  of 38 was lost to this once, before the fix.
- **The run dies halfway** — the database is now a partial run. Re-run from
  scratch; do not `--keep` on top of a broken run.
- **You want run 4 back** — restore from `.freeze/run4-backup/`, then re-render
  and re-publish.
