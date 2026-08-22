---
tags: [video, motion-design, reference, porchlight]
status: draft
created: 2026-08-21
---

# Motion design references — Part 1 ("The problem")

> Three reference clips watched frame-by-frame (refs/1.mp4, 2.mp4, 3.mp4) to brief
> Claude Design for recording [[VIDEO_SCRIPT]] §1 (0:00–0:45). Techniques only —
> palette and pacing are re-derived for [[BRANDING]]'s amber-on-dusk restraint rule
> below, not copied.

## What each reference contributes

**refs/3.mp4** (AE tutorial cold-open, first ~13s before the screen recording
starts): color-blocked title cards — charcoal → warm grey → bold blue → warm grey —
cut hard between beats, no crossfades. Mixed-weight type within one line (regular +
bold, sometimes a size jump) emphasizes a single word. One card animates the whole
phrase traveling and scaling up along a gentle arc path. A thin credit bar stays
pinned to the bottom edge across every card, unifying the sequence. A small
comet/dot used as decorative punctuation after a key word.

**refs/1.mp4** (40s "tips" short): a phrase builds one word at a time inside a
thin, hand-drawn-looking tilted oval that itself rotates slightly with each new
word. Cream background, bold rounded sans, single accent blue. Hard cut into an
unrelated pop-culture clip for one beat of humor, then back to type. Every
instruction step sits in a fixed caption zone below a big rounded-corner "device
card," changing every 1–2 seconds.

**refs/2.mp4** (editing-philosophy essay): sentence fragments scattered across the
frame at different rotations, not stacked, for a handwritten/collaged feel. A
keyword gets circled mid-sentence with a loose, hand-drawn red ellipse to flag the
point. Heavy whip-pan motion blur is the transition between beats instead of
crossfades. Long silent pauses on a plain background with one centered word for
comic/rhythmic timing.

## Adapted brief — paste into Claude Design

> Background stays #0B1120 (dusk) throughout — no color-block cuts. The
> "cut-between-solid-colors" trick becomes a cut between dusk and a barely-lighter
> "porch" (#141E33) card, not a hue change.
>
> No amber (#FFB454) anywhere in this beat. Nothing here is an escalation — amber
> is reserved for the one alert later in the video, so it must stay completely
> dormant now, or the restraint stops reading as restraint. Use Chalk (#E9EEF7) for
> the live report and Dim (#8FA0BC) for the other three once they're "read."
>
> Reports enter one at a time: each full report drops in as one line (not
> word-by-word — these are already-written texts, not a title card), lands with a
> small settle/overshoot, then immediately downshifts from Chalk to Dim as the next
> one arrives — visually banking it as "already logged."
>
> Borrow the hand-drawn-circle move, but in Chalk ink, never amber: circle or
> underline the differing noun in each report — mailboxes / post boxes / where the
> packages get dropped / delivery lockers — as it lands. Once all four are on
> screen, literally strike through all four in that same restrained line weight to
> land the "share no content word" point without narration competing for
> attention.
>
> Typography: system sans for the report lines (found text, not a title card);
> Georgia only for the final tagline card; monospace for any evidence/metric text.
>
> Pacing: hard cuts only, no crossfades — but slower than any of the three refs,
> roughly 8–10s per report across the 45s beat (4 reports + tagline card). Skip the
> whip-blur transitions entirely; Porchlight's argument is calm, not kinetic.
>
> End on the tagline card — "Porchlight — your friendly neighborhood agent" — in
> Georgia, Chalk on dusk, no motion flourish.

---

# Part 2 ("Who it's for") — 0:45–1:15

Same restraint rules as Part 1: dusk background, **no amber**, hard cuts only.

> [!warning] The Chalk→Dim downshift is spent
> Part 1 uses it to mean *"read and banked."* Using the same fade here to mean
> *"a human stopped reading"* would give one visual two opposite meanings
> forty-five seconds apart. Velocity and crowding carry this beat instead.

> [!note] Timing runs about 2 seconds long
> The narration below is 79 words. At a calm 150 wpm that is ~32s against a 30s
> slot. Either cut two clauses, or let §2 run to 1:17 and take it out of §3a's
> scroll, which has slack. Do not speed up the read — the calm is the point.

---

## Adapted brief — Part 2 — paste into Claude Design

> **CANVAS**
> 1920×1080, 30fps, 30 seconds (0:45–1:15 of a 5:00 video). The background is a
> flat fill `#0B1120` on every frame of this beat — it never changes hue, never
> gradients, never vignettes.
>
> **PALETTE — these five values only**
>
> | token | hex | use |
> |---|---|---|
> | dusk | `#0B1120` | the background, always |
> | porch | `#141E33` | card/panel fill, the only lighter surface |
> | chalk | `#E9EEF7` | live/primary text |
> | dim | `#8FA0BC` | secondary text — never a *transition target* in this beat |
> | line | `#243352` | hairlines and borders, 1px |
>
> **`#FFB454` amber is FORBIDDEN in this beat.** Not in text, not in a border,
> not in a glow, not at 5% opacity. It is reserved for a single alert at 2:35,
> and the restraint only reads as restraint if it stays completely dormant until
> then. Where a frame needs emphasis, use weight or size — never colour.
>
> **TYPE**
> - Channel messages: system sans (Inter / SF / Segoe), weight 400, 34px,
>   line-height 1.45, left-aligned. These are *found text* — they must look typed
>   by strangers, not designed.
> - `MUTED`: system sans, weight 600, 96px, letter-spacing `0.32em`, centred.
> - Closing lines: Georgia, 400, 46px, centred.
> - No monospace anywhere in this beat — nothing here is a metric.
>
> **LAYOUT**
> Messages sit in a left-aligned column: x = 260px, first baseline y = 300px,
> 92px of vertical rhythm between messages, max width 1180px. Nothing is centred
> except the two full-frame cards.
>
> ---
>
> ## SHOT 2A — the crowd builds · 0:45.0 → 0:56.0 (11.0s)
>
> Six messages arrive **accelerating**. Each is one line of plain text: no
> avatars, no bubbles, no timestamps, no UI chrome. Text alone on dusk.
>
> | # | text | enters at | gap to next |
> |---|---|---|---|
> | 1 | Anyone else hear that around 2am? | 0:45.6 | 2.4s |
> | 2 | Raccoon in the bins again | 0:48.0 | 1.9s |
> | 3 | Strange car parked on Oak all day | 0:49.9 | 1.4s |
> | 4 | Has anyone seen a grey cat? | 0:51.3 | 1.0s |
> | 5 | Fireworks? or something else?? | 0:52.3 | 0.7s |
> | 6 | Bins didn't get collected | 0:53.0 | — |
>
> The gaps shrink 2.4 → 1.9 → 1.4 → 1.0 → 0.7. That curve **is** the shot. If the
> messages arrive evenly the beat says nothing at all.
>
> **Per-message entrance (280ms):**
> - y: +18px → 0
> - opacity: 0 → 1
> - easing: `cubic-bezier(0.34, 1.56, 0.64, 1)` — a small settle/overshoot, the
>   same one Part 1 uses for its report drop, so both beats feel like one hand
>   made them
> - **all six stay at full chalk `#E9EEF7`.** No dimming, ever. They are not being
>   read and banked; they are piling up.
>
> **0:53.6 → 0:56.0 — the flood.** After message 6, more messages keep arriving,
> now every 90–130ms, and they are **deliberately illegible**: 40–70% of the width
> of the real ones, filled with plausible text at 34px that the eye cannot resolve
> at that speed. Once the column exceeds the frame it scrolls up **linearly** at
> ~340px/s, so lines push off the top edge as new ones enter at the bottom. Let
> 2–4 lines **overlap by 10–20px** near the end — the tidy rhythm should visibly
> break down. By 0:55.6 the frame is full of text nobody could read.
>
> No blur, no shake, no zoom. The frame stays locked. Density is the only effect.
>
> **HARD CUT at 0:56.0**, landing on the narrator's word *"mute."* Zero frames of
> transition.
>
> ---
>
> ## SHOT 2B — MUTED · 0:56.0 → 1:02.0 (6.0s)
>
> Full-frame dusk. One word, optically centred (nudge up ~2% from mathematical
> centre):
>
> **M U T E D**
>
> `#E9EEF7`, weight 600, 96px, letter-spacing `0.32em`. It is **already on screen
> at the cut** — it does not animate in. The cut is the animation.
>
> Then hold, completely still, for the full six seconds. No pulse, no drift, no
> breathing scale. Stillness after eleven seconds of accelerating clutter is the
> entire point of the beat, and any motion here spends it.
>
> Optional, only if six seconds of stillness tests as too long: at 0:59.0 draw a
> single 1px `#243352` hairline left-to-right beneath the word over 600ms, 420px
> wide, centred. Nothing else.
>
> **HARD CUT at 1:02.0.**
>
> ---
>
> ## SHOT 2C — what Porchlight sends instead · 1:02.0 → 1:12.0 (10.0s)
>
> Full-frame dusk, empty. Hold **1.2 seconds of nothing** — a completely blank
> dusk frame — before anything appears. That empty beat states the product thesis
> visually, and it is the most important 1.2 seconds in the section.
>
> At 1:03.2 one line appears, centred, Georgia 46px `#E9EEF7`:
>
> > most days it says nothing
>
> Entrance: opacity 0 → 1 over 400ms, `cubic-bezier(0.22, 1, 0.36, 1)`, **no
> movement** — it resolves in place. This is the brand line from the repo footer;
> it should feel like it was always there rather than like it arrived.
>
> Hold to 1:12.0. Nothing else enters the frame. Resist adding anything.
>
> ---
>
> ## SHOT 2D — the human in the loop · 1:12.0 → 1:15.0 (3.0s)
>
> Hard cut. Two lines, centred, stacked, Georgia 46px, 84px apart:
>
> > The agent drafts.
> > A person sends.
>
> - `The agent drafts.` is on screen at the cut, in dim `#8FA0BC`.
> - At 1:13.4, `A person sends.` appears in full chalk `#E9EEF7`: opacity 0 → 1
>   over 320ms, no movement.
>
> This is the one place dim-vs-chalk carries emphasis rather than state, and it
> works because both lines are on screen together — it reads as hierarchy, not as
> a transition. **Do not fade the first line down**; it starts dim and stays dim.
>
> Hold to 1:15.0, then hard cut into §3a.
>
> ---
>
> ## TRANSITION RULES FOR THE WHOLE BEAT
>
> - **Hard cuts only.** No crossfades, no dips to black, no whip-pans, no motion
>   blur between shots. The refs used whip-blur; it was deliberately dropped
>   because Porchlight's argument is calm, not kinetic.
> - The camera never moves. No push-in, no parallax, no drift.
> - Nothing loops, pulses or breathes while held.
> - Every entrance is ≤400ms. Nothing in this beat animates slowly.
>
> ## DO NOT
>
> - Do not use amber anywhere, at any opacity.
> - Do not fade the six channel messages to dim — that move means "read and
>   banked" in Part 1 and would contradict itself here.
> - Do not add app chrome: no phone frame, no chat bubbles, no avatars, no
>   notification badges, no status bar. Text on dusk, nothing else.
> - Do not add sound design to the crowd. The narration should be the only audio,
>   and the cut to MUTED should be the only place it pauses.
> - Do not put the logo in this beat. The mark appears at 4:30 and nowhere before.
>
> ## NARRATION SYNC
>
> | time | narration | on screen |
> |---|---|---|
> | 0:45.0 | *Porchlight is for everyone on the street — and what makes it worth having is what it doesn't send.* | messages 1–3 arriving |
> | 0:52.0 | *Most neighbourhood apps buzz for everything, so people mute them.* | messages 4–6, then the flood; **cut on "mute"** |
> | 0:56.0 | *Then the one that mattered lands in a channel nobody reads.* | MUTED, held |
> | 1:02.0 | *Porchlight goes straight to the residents of a zone, and most weeks it says nothing at all.* | empty dusk → "most days it says nothing" |
> | 1:08.0 | *The silence is what makes the rare message worth opening.* | same frame, held |
> | 1:12.0 | *A volunteer still approves every alert. The agent drafts. A person sends.* | the two-line card |

**Still unbriefed:** §3 (largely screen capture, so it may not need one), §4
(architecture — `assets/architecture.html` to work from) and §5 (the close).

---

## Housekeeping

- Source clips live in `refs/` — **reference only, never committed. They stay
  on the local machine permanently.** They are style references used to brief
  the motion work, not project assets, so there is nothing to hand over and
  nothing to clean up before submission.
- Enforced by `.gitignore` (`refs/`, `*.mp4`) after a `git add -A` swept all 698
  files into a commit on 2026-08-21. Caught before it was pushed.
- `refs/_to_delete/` holds scratch frame exports from this analysis pass; delete
  them whenever the disk space is wanted. Nothing depends on them.
