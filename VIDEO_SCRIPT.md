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
> The escalation judgment in offline mode is a hard-coded rule. Every decline in
> §3b — the seconds this whole video rests on — is a real model reading real
> evidence and refusing, and offline mode **structurally cannot show that**. The
> banner, the page band, and `publish.sh` all refuse it. The camera won't.

- [x] Real run completed, non-offline, all four behaviours confirmed — runs 3
      and 4, 2026-09-01. **Every figure below now comes from run 4.** The live/
      escalation reasoning is worded differently on every run; read the numbers,
      not the model's sentences
- [x] `out/report.html` generated from the same run as the terminal footage —
      they read the same rows through `models.outcome_of`, and a graph that
      contradicts the log is worse than no graph
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
| 1:15–3:30 | **The demo** | Terminal, live — ending on the transcript |
| 3:30–4:20 | Architecture | Diagram, then the graph |
| 4:20–5:00 | Why it matters | The graph, held, then the holdout |

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

> There has been **a guy** hanging around the **mailboxes** the last couple of
> evenings. Does not live in our building as far as I know.
>
> Saw someone loitering by the **post boxes** again tonight when I got back from
> work. Just stood there on their phone.
>
> Somebody was messing about near **where the packages get dropped** when I left
> this morning. Could not tell what they were doing.
>
> **Person** waiting around by the **delivery lockers** early on again. That is
> the third time this week someone has brought it up.

> [!danger] These are verbatim from `data/seed_reports.json`. Do not paraphrase
> An earlier draft of this beat wrote *"a person hanging around the mailboxes"*
> and *"A person was waiting around"*. The seed says **"a guy"** and
> **"Person waiting"**. That was harmless while §1 was the only place these
> reports appeared — but **§3d now puts the same four reports on screen with
> their real text**, so a paraphrase here means a judge sees one report worded
> two different ways inside three minutes.
>
> Re-check them against the file before the shoot:
> `python -c "import json;[print('-',r['text']) for r in json.load(open('data/seed_reports.json')) if 'locker' in r['text'] or 'mailbox' in r['text'] or 'post box' in r['text'] or 'packages get dropped' in r['text']]"`
>
> **Keep "a guy".** It is a person-description, it is exactly what triage strips,
> and §3d pays it off when the stored sentence beside it reads *"A person has
> been near the parcel lockers on multiple evenings."*

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

### 3b · The decline — 1:45–2:20

**On screen:** scroll back to the declined cluster. Show its `--explain`
reasoning and hold on it.

> [!danger] Rewritten 2026-09-02 — the old version described a decline that does not happen
> This beat used to open on the near-miss: *"three people, three zones, three
> weeks, declined on the spread."* **The agent never does that.** Retrieval
> never links those three to each other — they sit at 0.436–0.456 similarity,
> while one of them scores 0.576 against a completely unrelated report. They are
> logged silently, one at a time, and no cluster is ever assembled for the
> escalation agent to refuse. Reading the old narration over a live run would be
> narrating something the terminal does not show.
>
> What survives is the **single-reporter** decline, which is the stronger case
> anyway: it is the one where the agent has a real, tight, plausible cluster in
> front of it and says no.

**Narration** *(~95 words)*

> Now the interesting part — what it found, and still didn't send.
>
> Four reports here. One zone. A few days. All describing the same kind of
> thing. The agent grouped them, checked who filed them — and found one name.
>
> Four reports from one person is not four people agreeing. It's one neighbour's
> repeated worry. And treating that as a neighbourhood pattern is exactly how a
> service like this gets used against somebody.
>
> Declined. Nobody hears about it. Nobody gets talked about.

> [!tip] Slow down here
> This is the most persuasive twenty seconds in the video. A system that only
> ever fires isn't exercising judgment — the decline is what makes the alert
> worth reading. Let the reasoning text sit on screen long enough to actually be
> read, and resist adding a second decline to pad it. There is one.

> [!note] If you want the near-miss on camera, this is the honest framing
> Optional, ~10s, only if §3 is running short: *"Three more looked similar to
> each other and never even grouped — different streets, three weeks apart. The
> agent never had to refuse them, because it never assembled them."* That is
> true, it is in the README, and it is a weaker beat than the decline. Cut it
> first if you are over.

### 3c · The alert — 2:20–3:05

**On screen:** the parcel-locker cluster escalating. Show the alert, the
evidence line, and the escalation agent's reasoning. Then scroll on to the
**fourth** report of the same cluster arriving and being suppressed.

> [!warning] The evidence line is 3 / 3 / 13 hours, not 4 / 4 / 36
> It alerts on the **third** report — 3 reports, 3 distinct reporters, 13 hours,
> z = 6.5. The 4/4/36-hour state belongs to the report that is *suppressed*,
> and the cluster's final z is 9.0. All three numbers were wrong on every
> surface until 2026-09-01; don't reintroduce them here. Read them off the
> terminal on the day.

**Narration** *(~110 words)*

> And then this.
>
> Three reports. Three different people. One zone. Thirteen hours. And a report
> rate this street does not normally see.
>
> That's the cluster from the opening — the ones that share no words. The agent
> found them by meaning, weighed how many separate people filed them and how
> tightly grouped they were, and decided this one is worth interrupting a human
> for.
>
> Then a fourth report arrives. Same place, same pattern. It does not alert
> again — that situation is already open, and the neighbourhood has already been
> told.
>
> One alert. Out of thirty-eight reports.

### 3d · What it kept — 3:05–3:30

**On screen:** the two-column transcript section of `out/report.html` — what
each neighbour typed on the left, the single sentence Porchlight stored on the
right. Four rows, all resolving to the same right-hand side.

> [!important] Added 2026-09-02. This is the best visual in the project
> Four phrasings with no shared content word collapsing into one identical
> stored sentence — it proves the premise from §1 *and* the redaction claim in
> one frame, without a word of explanation. It did not exist when this script
> was written. Its 25 seconds come out of §3b (one decline, not two) and §4
> (trimmed to 50s), so the running time is unchanged.
>
> Generate the page with `--show-raw`; `raw_text` is off by default at all three
> boundaries, which is the point of the beat and worth one sentence if asked.

**Narration** *(~70 words)*

> And look at what it kept.
>
> On the left, what four neighbours actually typed. On the right, the one
> sentence Porchlight stored for each of them.
>
> Same place, four ways of saying it, no word in common. And every description
> of a person is gone.
>
> That isn't a promise the prompt makes. It's enforced in code, with a retry,
> before the text ever reaches the database. The alert names a place to watch —
> never a person to look for.

---

## 4 · Architecture — 3:30–4:20

**On screen:** `assets/architecture.html`, held for the whole beat.

> [!note] Unblocked 2026-09-01 — the page on disk is now live and current
> This beat used to warn the report page off camera: it had been rendered
> `--offline` on 2026-08-19 with the hard-coded escalation stub, and it predated
> the tally fix. **Both are resolved.** `out/report.html` is run 4, live, and
> both surfaces now bucket through `models.outcome_of`, so the page and the
> terminal cannot disagree.
>
> The page's fifteen-second cut has moved to **§3d**, where it does more work.
> This beat is now the diagram alone, trimmed 60s → 50s to pay for that. Nothing
> in the narration below refers to the graph, so the trim is a cut, not a rewrite.

**Narration** *(~140 words — drop the tool list if you land over 50s)*

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

## 5 · Why it matters — 4:20–5:00

**On screen:** the correlation graph, held. Most of it dim and unconnected; one
cluster lit amber and linked.

**Narration** *(~105 words)*

> We checked whether a similarity threshold could do this instead. It can't —
> the near-miss reports resemble each other *less* than one of them resembles a
> completely unrelated report about a car. There's no cutoff that separates them.
>
> Telling those apart takes reading them. That's why there's an agent here.
>
> And we tested it honestly. Twenty reports, written before any tuning began,
> held back, and run once at the end — including a bike theft nobody described
> the same way, and four reports that all say "parked car on Sycamore Row" and
> have nothing to do with each other. Twenty out of twenty.
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
- Any claim about the holdout beyond what §5 says. It ran once, on 2026-08-31,
  and **must not be re-run** — a second run after any prompt change turns it into
  tuning data and the number stops meaning anything
- The word "declines" about the near-miss. It is never correlated, so it is
  never refused. §3b's callout has the wording that is true

**The holdout is now in §5**, not optional — it is the strongest credibility
claim available and it costs fifteen seconds. If asked what it does *not* prove:
the run produced zero declines, so it shows the agent finding a hard cluster and
resisting a lexical trap, not refusing a plausible one. That caveat is in the
README and the Devpost text; don't hide it and don't narrate it.

**Recording:** slides, screen capture, and voiceover are all explicitly
acceptable. You do not need to appear on camera. Re-shoots are safe — node
positions are seeded from `report_id`, so the graph doesn't move between takes.
