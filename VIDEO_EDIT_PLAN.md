---
tags: [video, edit, capcut, hackathon, porchlight]
status: active
created: 2026-09-10
updated: 2026-09-11
---

# Edit plan and timings

> The cutting order for CapCut, the exact length of every clip, and the
> narration trimmed to fit five minutes. Story and intent are
> [[VIDEO_SCRIPT_STORY]]; commands for the demo are [[SHOOT_RUNBOOK]].
>
> **Nothing here is generated video.** Every non-terminal shot is a motion
> graphic drawn from the project's own data, so the text stays legible and the
> numbers stay true. Two files produce all of it:
>
> ```
> .venv\Scripts\python.exe scripts/make_opening.py --open   # the four reports
> .venv\Scripts\python.exe scripts/make_scenes.py --open    # everything else
> ```

---

## The narration was 1038 words. It is 558 here.

Counted from [[VIDEO_SCRIPT_STORY]] on 2026-09-10: **1038 words**, which is
**6:40 at 155 wpm and 7:40 at 135**. Against a hard five minute limit. The note
in that file claiming about 660 words was wrong.

This plan is **558 words across 4:51**: about 4:18 of speech and **33 seconds of
deliberate silence**, most of it while the four reports are on screen and while
the terminal scrolls. Every clip has been checked for speaking rate and none
asks for more than **126 words per minute**, which is unhurried. Record from the
lines here, not from the long version.

---

## The timeline

**4:51 total.** Trim each clip to exactly these lengths.

| # | Source | Length | In | Out | Words |
|---|---|---|---|---|---|
| 1 | `scenes.html` 1, the street | 7s | 0:00 | 0:07 | 10 |
| 2 | `opening.html` | 47s | 0:07 | 0:54 | 85 |
| 3 | `scenes.html` 2, the burden | 24s | 0:54 | 1:18 | 50 |
| 4 | Terminal, reports scrolling | 18s | 1:18 | 1:36 | 30 |
| 5 | Terminal, the refusal | 38s | 1:36 | 2:14 | 80 |
| 6 | Terminal, the alert | 38s | 2:14 | 2:52 | 76 |
| 7 | `report.html`, transcript | 31s | 2:52 | 3:23 | 64 |
| 8 | `architecture.html` | 28s | 3:23 | 3:51 | 56 |
| 9 | `report.html`, the graph | 20s | 3:51 | 4:11 | 34 |
| 10 | `scenes.html` 3, the tally | 17s | 4:11 | 4:28 | 32 |
| 11 | `scenes.html` 4, the lamp | 14s | 4:28 | 4:42 | 24 |
| 12 | `scenes.html` 5, end card | 9s | 4:42 | 4:51 | 17 |

Four clips are motion graphics, one is the opening animation, six are real
screen recordings, and the last is a card. Nothing is filmed and nothing is
generated.

---

## Recording the graphics

`scenes.html` holds five scenes in one page. **Keys 1 to 5 pick a scene, space
plays or replays it, h hides the hint.** Record each separately, browser full
screen at 1920x1080, then trim to the length in the table.

`opening.html` is its own file: space plays, h hides.

Both scale a fixed 1920x1080 stage to the window, so what you record is what was
composed rather than whatever the browser reflowed.

---

## Clip 1 · The street

**7 seconds.** `scenes.html`, scene 1.

A line of houses draws itself across the frame and a few messages lift off it as
small blue dots and drift away unread. Warm paper, no amber.

**Narration** *(10 words, 86 wpm)*

> My street has a group chat. Yours probably does too.

---

## Clip 2 · The four reports

**47 seconds.** `opening.html`. Trim about four seconds off the head, since
clip 1 has already established the street.

The chat fills up, everything hushes when it is muted, the four that matter rise
in front of the blurred noise, each place name is ringed and then struck
through, and the four names collapse into one place. Ends by turning to dusk,
which is the cut into everything after it.

**Narration** *(85 words, 109 wpm)*

Speak over the pile-up, then **stop while the four reports are on screen**. Let
them be read. Come back for the last two lines over the rings and the strike.

> A pothole. The street light is out again. Bins blocking the alley. Fireworks
> last night, waking the baby. It goes all day.
>
> So I muted it. Everyone I know has muted it. And that is the problem, because
> that chat is also where you would find out if something was actually going on.
>
> Four messages. Four different people. About a day and a half.

*(silence, roughly 20 seconds, while the four land)*

> Mailboxes. Post boxes. Where the packages get dropped. Delivery lockers. Same
> place four times, and not one word in common.
>
> Nobody in that chat is going to catch that. I would not have.

---

## Clip 3 · The burden

**24 seconds.** `scenes.html`, scene 2.

Thirty four messages stream in from every edge of the frame and converge on a
single circle in the middle, which is the one person meant to read all of it.
The circle takes on a load ring as they arrive. Caption underneath: *one person,
reading all of it*.

**Narration** *(50 words, 125 wpm)*

> The person who is meant to catch this is a volunteer. A block captain, someone
> who moderates a local server, whoever ended up with the job.
>
> They are not paid and they already have too much on. The alternative to
> somebody reading everything is that nobody does.

---

## Clip 4 · Terminal, the reports scrolling

**18 seconds.** Real recording. Speed-ramp the middle of the run to fit.

**Narration** *(30 words, 100 wpm)*

> Thirty eight reports go in. Watch what mostly happens.
>
> Nothing. Thirty seven of them never reach a single person. That is not it
> failing to do its job. That is the job.

---

## Clip 5 · Terminal, the refusal

**38 seconds.** The Birch Ln block in the reasoning section. Hold still on it.

**Narration** *(80 words, 126 wpm)*

> This is the part I care about. Something it found, and did not send.
>
> Four reports. Four different people. One street. A van left running. Someone
> looking into parked cars.
>
> Four separate neighbours is real corroboration. Any threshold would have fired.
> But three weeks apart, and the last one twelve days after the one before.
>
> Here is what it said.

*(let the reasoning sit on screen, then read its last line)*

> Four people each saw one thing, weeks apart, that looked a bit odd to them.
> That is a street, not a situation.
>
> Declined. Nobody hears about it.

---

## Clip 6 · Terminal, the alert

**38 seconds.** The pattern block, the approval prompt, then the fourth report
being held back.

**Narration** *(76 words, 120 wpm)*

> And then this one.
>
> Three reports. Three different people. Thirteen hours. And a rate of reporting
> that street does not normally see.
>
> That is the cluster from the opening. The four that share no words. It found
> them by meaning, counted how many separate people filed them, and decided this
> one was worth interrupting somebody for.
>
> It does not send it on its own. It drafts it and asks.

*(type y)*

> Then a fourth arrives about the same place, and it does not alert again.
>
> One alert. Out of thirty eight.

---

## Clip 7 · The transcript

**31 seconds.** `out/report.html`, the two column section. The Replay button
re-runs the reveal, so take it as often as you like.

**Narration** *(64 words, 124 wpm)*

> Now look at what it kept. On the left, what people typed. On the right, what
> Porchlight stored.
>
> The one at the top is a broken locker door. Same street as the cluster. Logged,
> and nobody hears about it.
>
> Then those four. Four ways of saying it, no word in common, one place.
>
> And every description of a person is gone. That is enforced in code.

---

## Clip 8 · Architecture

**28 seconds.** `assets/architecture.html`, held.

**Narration** *(56 words, 120 wpm)*

> Three agents, in order, on the Strands SDK and Bedrock.
>
> Haiku reads one report and rewrites it as a neutral sentence with the person
> taken out. That sentence is the only copy that lasts.
>
> Sonnet works out which reports are the same situation. It never returns a
> count. The counting is code.
>
> Opus decides.

---

## Clip 9 · The graph

**20 seconds.** `out/report.html`, the map of the run, held.

**Narration** *(34 words, 102 wpm)*

> I checked whether a similarity score could do this instead. It cannot. The
> reports I wrote to look alike score lower against each other than against
> unrelated ones.
>
> Telling them apart means reading them.

---

## Clip 10 · The tally

**17 seconds.** `scenes.html`, scene 3.

Thirty eight marks appear one at a time, all of them go quiet, and one lights
amber with a halo. The numbers are counted from `porchlight.db`, so this cannot
drift from the terminal or the report page.

**Narration** *(32 words, 113 wpm)*

> And I tested it honestly. Twenty reports, written before I tuned anything, run
> once at the end. Twenty out of twenty.
>
> It refused nothing in that run, so it does not prove it can turn one down.

---

## Clip 11 · The lamp

**14 seconds.** `scenes.html`, scene 4.

The project's own porch light mark, drawn in outline on dusk, and then lit. The
glow blooms out behind it. Caption: *most weeks, nothing at all*.

This is the only place amber arrives in full, and it comes after the alert, so
the restraint has already earned it.

**Narration** *(24 words, 103 wpm)*

> Porchlight reads every report so nobody has to, and tells a street the one
> thing worth knowing.
>
> Which most weeks is nothing at all.

---

## Clip 12 · End card

**9 seconds.** `scenes.html`, scene 5. Wordmark, tagline, repo and live link.

**Narration** *(17 words, 113 wpm)*

> It is on GitHub, MIT licensed, and that report is live. Every report in it is
> invented.

---

## CapCut assembly

**Project at 1920x1080, 30fps.** All the graphics are screen recordings, so
everything is already the same frame rate and colour space. Set it once.

**Cut picture first, record narration against it.** The timings assume the cut
exists. Recording voice to a stopwatch and building picture around it is how
videos end up forty seconds long.

**Do not grade anything.** Every shot is either a screen recording of the real
tool or a graphic already built in the brand palette. There is nothing to match
and nothing to fix.

**Sound.** Room tone or a very quiet pad underneath so the silences do not read
as dropouts. Nothing with a beat. The argument here is calm and music that
pushes will fight it.

**Transitions.** Hard cuts throughout. The one exception is clip 2 into clip 3,
where the animation has already gone to dusk, so a short dissolve reads as one
move rather than two.

**Before export.** Total under 5:00 with the end card included.
