---
tags: [video, submission, hackathon, porchlight]
status: draft
created: 2026-08-20
---
 
# Demo video — shooting script

> Five minutes maximum, public on YouTube or Vimeo. Must demonstrate the working
> project **and** pitch (1) the problem (2) who it's for (3) why it matters —
> all three are named requirements, not suggestions.
>
> Structure follows [[PROJECT_BRIEF]] §10. Companion to [[CHECKLIST]] §4.

---

## Before you record

> [!danger] Never record `--offline`
> The escalation judgment in offline mode is a hard-coded rule, and the near-miss
> decline — the twenty seconds this whole video rests on — is the one thing
> offline mode **structurally cannot show**. The banner, the page band, and
> `publish.sh` all refuse it. The camera won't.

- [ ] Real run completed, non-offline, all four behaviours confirmed
- [ ] **Re-check every number in this script against that run.** The figures
      below come from the offline run and the seed data; the live escalation
      reasoning will be worded differently and the anomaly score may shift
- [ ] `out/report.html` generated from the same run as the terminal footage —
      they read the same rows, and a graph that contradicts the log is worse
      than no graph
- [ ] Terminal at a readable size. Dark background, per [[BRANDING]]
- [ ] Font large enough to survive YouTube compression — test at 1080p before
      committing to a take
- [ ] `FNA_TRACE` unset, so the output stays clean

**Timing budget.** ~630 words of narration at a measured 140–150 wpm, leaving
room to stop talking and let the demo play. Word counts are marked per section;
if you overrun, cut from §4, never from §3.

---

## Beat sheet

| Time | Beat | What's on screen |
|---|---|---|
| 0:00–0:45 | The problem | Four reports, side by side |
| 0:45–1:15 | Who it's for | The coordinator |
| 1:15–3:30 | **The demo** | Terminal, live |
| 3:30–4:30 | Architecture | Diagram, then the graph |
| 4:30–5:00 | Why it matters | The graph, held |

---

## 1 · The problem — 0:00–0:45

> [!tip] Detailed motion direction for this beat lives in [[MOTION_REFS]]
> Cut-by-cut: reports drop in as Chalk and downshift to Dim as the next arrives,
> hand-drawn circles on the differing nouns, strike-through on all four to land
> the "no shared words" point, hard cuts only, ~8–10s per report. **No amber in
> this beat** — it is reserved for the single alert in §3c, and the restraint
> only reads as restraint if it stays dormant until then.

**On screen:** the four cluster reports appearing one at a time, as plain text,
the way they'd arrive in a group chat. Highlight the four different phrases for
the same place as each lands.

> There has been a person hanging around the **mailboxes** the last couple of evenings.
>
> Saw someone loitering by the **post boxes** again tonight when I got back from work.
>
> Somebody was messing about near **where the packages get dropped** when I left this morning.
>
> A person was waiting around by the **delivery lockers** early on again.

**Narration** *(~105 words)*

> Four neighbours. One day and a half. The same parcel lockers, in the same
> building.
>
> They describe it four different ways — mailboxes, post boxes, where the
> packages get dropped, delivery lockers. Those four reports share no content
> word at all.
>
> So any keyword filter sees four unrelated notes. And a human reading them a
> day apart, in a channel with thirty other messages, sees four unrelated notes
> too.
>
> The pattern is real. Nobody is positioned to notice it.
>
> This is Porchlight — your friendly neighborhood agent. It notices. And, more
> importantly, it declines to notice patterns that aren't there.

> [!tip] Land the "no shared words" point hard
> It's the whole premise, it's verifiable on screen in four seconds, and every
> judge will immediately understand why keyword matching fails. Consider
> literally striking through the four phrases to show nothing matches.

---

## 2 · Who it's for — 0:45–1:15

**On screen:** plain text on the dusk background, same treatment as §1 — no
b-roll, no phone mockup. Six ordinary neighbourhood-channel messages arrive,
**accelerating** — the first two land at a readable pace, then they come faster
and start overlapping and pushing off the top of the frame. Hard cut on the
crowd to a near-empty dusk frame with one word: **MUTED**.

> [!warning] Do not fade these to Dim — that move is taken
> [[MOTION_REFS]] gives §1 a Chalk→Dim downshift meaning *"read and banked."*
> Reusing the same fade here for *"a human stopped reading"* gives one visual
> two opposite meanings forty-five seconds apart. Volume is the argument in this
> beat, so let velocity and crowding carry it and keep the fade out of it.
>
> **No amber**, same rule as §1 — nothing here is an escalation.

The hard cut into an almost-empty frame also sets up §3a, which opens on quiet.

> Anyone else hear that around 2am?
>
> Raccoon in the bins again
>
> Strange car parked on Oak all day
>
> Has anyone seen a grey cat?
>
> Fireworks? or something else??
>
> Bins didn't get collected

Hold the muted state for a beat before cutting. The fade is the argument — the
narration says people mute these channels, and the screen shows it happening
rather than asserting it.

**Narration** *(79 words — see the timing note below)*

> Porchlight is for everyone on the street — and what makes it worth having is
> what it doesn't send.
>
> Most neighbourhood apps buzz for everything, so people mute them. Then the one
> that mattered lands in a channel nobody reads.
>
> Porchlight goes straight to the residents of a zone, and most weeks it says
> nothing at all. The silence is what makes the rare message worth opening.
>
> A volunteer still approves every alert. The agent drafts. A person sends.

> [!note] This beat runs about 2 seconds long
> 79 words at a calm 150 wpm is ~32s against a 30s slot. Either cut two more
> clauses or let §2 run to 1:17 and take it out of §3a's scroll, which has slack.
> **Don't solve it by reading faster** — the calm is the argument.
>
> Two words carry a cut: *"mute"* at 0:56 and the pause before *"nothing at
> all."* [[MOTION_REFS]] Part 2 has the full frame-level sync table.

> [!note] The audience changed on 2026-08-21 and this beat changed with it
> Alerts used to go to a single block captain, which made *them* the customer.
> They now broadcast to a zone's residents, so the volunteer is no longer the
> beneficiary — they are the **control**, the human in the loop. The people the
> product is for are the residents who muted their neighbourhood app.
>
> Don't reintroduce "this is built for the person who runs the channel." It
> contradicts `Audience = Literal["zone_residents"]` and the README's safety
> section, and a judge who reads the repo will notice.

---

## 3 · The demo — 1:15–3:30

> [!important] This is the section that decides the submission
> Two minutes fifteen. Let it breathe — silence while reports scroll is fine and
> reads as confidence. The three moments below are the point; everything else is
> texture.

**On screen:** terminal, `python demo/run_demo.py --explain`

### 3a · The quiet — 1:15–1:45

Let thirty-odd reports scroll past. Don't narrate over all of it.

**Narration** *(~55 words)*

> Thirty-eight reports go in. Watch what mostly happens.
>
> Nothing.
>
> Thirty-seven of them never surface to anyone. No alert, no notification,
> nobody woken. That's not the system failing to act — that's the product. Most
> days, a neighbourhood is fine, and a service that says so is worth more than
> one that doesn't.

> [!warning] Only two numbers in this video are fixed: **38 in, 1 alert out**
> The split between *silent* and *correlated-but-declined* depends on the calls
> the model makes on the day, and it has already been written down three
> different ways across this repo (34/3, 31/5, 29/7). All three agree on 37
> never surfacing, because a decline reaches nobody either — so say **37 of 38**
> and never quote the split in narration. `tests/test_pipeline.py` asserts
> exactly one alert; nothing asserts the split. If you want the breakdown on
> screen, let the terminal's own summary line show it and don't read it aloud.

### 3b · The declines — 1:45–2:35

**On screen:** scroll back to the two declined clusters. Show the `--explain`
reasoning for each.

**Narration** *(~110 words)*

> Now the interesting part — the times it found something and still said
> nothing.
>
> Here, three people reported similar-sounding activity. But across three
> different zones, spread over three weeks. The agent's own reasoning: too far
> apart, in space and in time, to be one situation. Three separate incidents
> that happen to resemble each other. Declined.
>
> And here, four reports, one zone, tight window — but all four from the same
> person. That's not corroboration. That's one neighbour's repeated concern, and
> treating it as a neighbourhood pattern is exactly how a service like this gets
> used against somebody. Declined.

> [!tip] Slow down here
> This is the most persuasive twenty seconds in the video. A system that only
> ever fires isn't exercising judgment — the declines are what make the alert
> worth reading. Let the reasoning text sit on screen long enough to actually
> be read.

### 3c · The alert — 2:35–3:30

**On screen:** the parcel-locker cluster escalating. Show the alert, the
evidence line, and the escalation agent's reasoning.

**Narration** *(~115 words)*

> And then this.
>
> Four reports. Four different people. One zone. Thirty-six hours. And a report
> rate this zone doesn't normally see.
>
> That's the cluster from the opening — the four that share no words. The agent
> found them by meaning, weighed who reported and how tightly grouped it was,
> and decided this one is worth interrupting a human for.
>
> One alert. Out of thirty-eight reports.
>
> And notice what the alert says: a place to watch. Not a person to look for.
> Descriptions of people are stripped before anything is stored — and that isn't
> a promise the prompt makes, it's enforced in code, with a retry, before the
> text ever reaches the database.

---

## 4 · Architecture — 3:30–4:30

**On screen:** `assets/architecture.html` for the full minute.

> [!danger] Do not shoot `out/report.html` yet — shoot the diagram for all 60s
> This beat used to end on a fifteen-second cut to the run report. That cut is
> **deferred until after the first live run**, for two reasons:
>
> 1. The page on disk was generated **2026-08-19 from an offline run**. Its
>    escalation is the hard-coded stub, so putting it on camera is recording
>    `--offline` by the back door.
> 2. It predates the tally fix. It reads `31 logged silently · 6 correlated and
>    declined`, while the terminal for that same run printed `5 declined ·
>    1 suppressed`. Both surfaces now share `models.outcome_of`, but **this file
>    was rendered before that** and still shows the old split.
>
> Regenerate it from the live run, then shoot the cut as a pickup and drop it in.
> The narration below already works without it — nothing in the words refers to
> the graph.

**Narration** *(~140 words)*

> Three Strands agents, in sequence.
>
> Triage reads one report on Haiku, classifies it, and rewrites it as one neutral
> sentence with every person-identifying detail removed. That sentence is the
> only long-lived copy.
>
> Correlation runs on Sonnet, with three tools — semantic search over past
> reports, a per-zone anomaly check, and zone history. It decides what's related
> and says why.
>
> Then the pipeline — not the model — counts the evidence. How many reports, how
> many *distinct* reporters, over what span. A safety control a model reports on
> itself isn't a control.
>
> Escalation weighs that on Opus and makes the call. It lives in the agent's
> reasoning, never in an `if count > 3` branch.
>
> Two independent signals: what the reports mean, and whether this place is
> genuinely busier than its own history.

> [!note] If you're over time, this is where to cut
> Drop the tool-by-tool detail and keep the three-agent shape plus the
> counted-not-reported point. Those are the two things a technical judge is
> listening for.

---

## 5 · Why it matters — 4:30–5:00

**On screen:** the correlation graph, held. Most of it dim and unconnected; one
cluster lit amber and linked.

**Narration** *(~75 words)*

> We checked whether a similarity threshold could do this instead. It can't —
> the near-miss reports resemble each other *less* than one of them resembles a
> completely unrelated report about a car. There's no cutoff that separates them.
>
> Telling those apart takes reading them. That's why there's an agent here.
>
> Small-scale community safety runs on volunteers with no tooling at all.
> Porchlight reads every report so nobody has to, and tells a street the one
> thing worth knowing — most weeks, that's nothing at all.

**Final frame:** the Porchlight mark. *your friendly neighborhood agent.*
Repo URL on screen.

---

## Notes

**Don't say on camera:**
- "Spider-Man", "Spidey", or any Marvel reference — [[BRANDING]] § *Trademark
  scope*. The phrase "friendly neighborhood" on its own is fine
- Any claim about the holdout unless you've run it. If you have, one sentence in
  §5 is worth more than any adjective in the whole script

**Worth adding if you land under 4:30:** the holdout result. Twenty reports
written before any tuning, run once at the end, reported honestly. It's a
stronger credibility claim than anything else available and it costs fifteen
seconds.

**Recording:** slides, screen capture, and voiceover are all explicitly
acceptable. You do not need to appear on camera. Re-shoots are safe — node
positions are seeded from `report_id`, so the graph doesn't move between takes.
