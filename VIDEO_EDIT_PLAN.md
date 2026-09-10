---
tags: [video, edit, capcut, seedance, hackathon, porchlight]
status: active
created: 2026-09-10
---

# Edit plan, timings and generation prompts

> The cutting order for CapCut, the exact length of every clip, the Seedance
> prompts for the generated shots, and the narration trimmed to fit five
> minutes. Story and intent are [[VIDEO_SCRIPT_STORY]]; commands are
> [[SHOOT_RUNBOOK]].
>
> Every clip below was checked for speaking rate. No clip asks for more than
> **135 words per minute**, which is an unhurried talking pace with room to
> breathe. If a line still feels rushed on the day, cut words rather than
> speeding up.

---

## Two things that decide the whole edit

### The narration was 1038 words. It is 561 here.

Counted from [[VIDEO_SCRIPT_STORY]] on 2026-09-10: **1038 words**, which is
**6:40 at 155 wpm and 7:40 at 135 wpm**. Against a hard five minute limit. The
header in that file claimed about 660 words and was wrong.

This plan uses **561 words across 4:52 of picture**: about 4:09 of speech and
**43 seconds of deliberate silence**, most of it while the four reports are on
screen and while the terminal scrolls. Record from the lines in this file, not
from the long version.

### Seedance cannot render text, so it cannot be the demo

Every generative video model turns text into convincing-looking gibberish.
Everything this project is about lives in text that has to be readable: the four
reports word for word, the evidence lines, the reasoning the model wrote, the
terminal. Generated footage of a terminal would also be footage of something
that is not the project, and the rules ask for a working demonstration.

| | Source |
|---|---|
| Anything where the words matter | Real screen recording, or `assets/opening.html` |
| The world around it | Seedance |

**Every prompt below ends by forbidding text in frame.** If a clip comes back
with signage, a legible screen or a readable noticeboard, generate it again.
Garbled text is the fastest way to make a submission look cheap.

---

## The timeline

**4:52 total.** Trim each clip to exactly these lengths in CapCut.

| # | Source | Length | In | Out | Words |
|---|---|---|---|---|---|
| 1 | Seedance A, the street | 7s | 0:00 | 0:07 | 10 |
| 2 | `assets/opening.html` | 51s | 0:07 | 0:58 | 85 |
| 3 | Seedance B, the volunteer | 14s | 0:58 | 1:12 | 29 |
| 4 | Seedance C, the noticeboard | 10s | 1:12 | 1:22 | 21 |
| 5 | Terminal, reports scrolling | 20s | 1:22 | 1:42 | 30 |
| 6 | Terminal, the refusal | 40s | 1:42 | 2:22 | 80 |
| 7 | Terminal, the alert | 36s | 2:22 | 2:58 | 76 |
| 8 | `out/report.html`, transcript | 30s | 2:58 | 3:28 | 64 |
| 9 | `assets/architecture.html` | 30s | 3:28 | 3:58 | 56 |
| 10 | `out/report.html`, the graph | 32s | 3:58 | 4:30 | 69 |
| 11 | Seedance D, the porch light | 14s | 4:30 | 4:44 | 24 |
| 12 | End card | 8s | 4:44 | 4:52 | 17 |

Generated footage is 45 seconds of 292. That is the right proportion. More of it
means less demonstration, and demonstration is what is being judged.

---

## Clip 1 · Seedance A, the street

**7 seconds.** Trim from whatever comes back, keeping the calmest middle.

```
A slow dolly push forward down a quiet residential street in late afternoon.
Low golden sun rakes across parked cars, hedges and a row of front doors, throwing
long soft shadows onto the pavement. Nobody in frame. Shallow depth of field,
35mm lens, very gentle handheld float, no fast movement. Warm cream and dusty blue
palette, muted saturation, soft natural film grain, 24fps cinematic.
Calm, ordinary, slightly empty.
No text anywhere, no signage, no house numbers, no screens, no logos.
```

**Narration** *(10 words, 86 wpm)*

> My street has a group chat. Yours probably does too.

---

## Clip 2 · The opening animation

**51 seconds.** Not generated. Run and screen-record it:

```
.venv\Scripts\python.exe scripts/make_opening.py --open
```

Space plays, h hides the hint. Record the browser full screen at 1920x1080.

This beat carries the four reports, so the text has to be real. It also ends by
turning to dusk, which is the cut into the rest of the video.

**Narration** *(85 words, 100 wpm)*

Speak over the pile-up, then **stop while the four reports are on screen**. Let
them be read. Come back for the last two lines over the rings and the strike.

> A pothole. The street light is out again. Bins blocking the alley. Fireworks
> last night, waking the baby. It goes all day.
>
> So I muted it. Everyone I know has muted it. And that is the problem, because
> that chat is also where you would find out if something was actually going on.
>
> Four messages. Four different people. About a day and a half.

*(silence, roughly 21 seconds, while the four land)*

> Mailboxes. Post boxes. Where the packages get dropped. Delivery lockers. Same
> place four times, and not one word in common.
>
> Nobody in that chat is going to catch that. I would not have.

---

## Clip 3 · Seedance B, the volunteer

**14 seconds.**

```
Medium close shot of a person sitting at a kitchen table late in the evening, lit
only by one warm table lamp and the cool glow of a laptop. They are scrolling
slowly with one hand, chin resting on the other, tired. Face turned away from
camera or cropped above the eyeline, not identifiable. Slow push in, 50mm lens,
shallow depth of field, laptop screen thrown completely out of focus.
Deep blue evening window behind, low warm practical light in front.
Muted filmic palette, soft grain, 24fps cinematic, very slow.
No readable text, no readable screen, no logos, no brand marks.
```

**Narration** *(29 words, 124 wpm)*

> The person who is meant to catch this is a volunteer. A block captain, someone
> who moderates a local server, whoever ended up with the job.

---

## Clip 4 · Seedance C, the noticeboard

**10 seconds.**

```
Static locked-off shot of a weathered wooden community noticeboard on a
residential street at blue hour. A few curled paper notices are pinned to it, one
corner lifting in a light breeze. Deep blue evening light, a single warm
streetlight far out of focus behind. 85mm lens, shallow depth of field, no camera
movement at all. Muted palette, soft grain, 24fps cinematic.
The notices are blank and completely illegible, blurred paper only.
No text, no writing, no signage, no logos.
```

**Narration** *(21 words, 126 wpm)*

> They are not paid and they already have too much on. The alternative to
> somebody reading everything is that nobody does.

---

## Clip 5 · Terminal, the reports scrolling

**20 seconds.** Real recording. Speed-ramp the middle of the run to fit.

**Narration** *(30 words, 90 wpm)*

> Thirty eight reports go in. Watch what mostly happens.
>
> Nothing. Thirty seven of them never reach a single person. That is not it
> failing to do its job. That is the job.

---

## Clip 6 · Terminal, the refusal

**40 seconds.** The Birch Ln block in the reasoning section. Hold still on it.

**Narration** *(80 words, 120 wpm)*

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

## Clip 7 · Terminal, the alert

**36 seconds.** The pattern block, the approval prompt, then the fourth report
being held back.

**Narration** *(76 words, 127 wpm)*

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

## Clip 8 · The transcript

**30 seconds.** `out/report.html`, the two column section. The Replay button
re-runs the reveal, so take it as often as you like.

**Narration** *(64 words, 128 wpm)*

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

## Clip 9 · Architecture

**30 seconds.** `assets/architecture.html`, held.

**Narration** *(56 words, 112 wpm)*

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

## Clip 10 · The graph

**32 seconds.** `out/report.html`, the map of the run, held.

**Narration** *(69 words, 129 wpm)*

> I checked whether a similarity score could do this instead. It cannot. The
> reports I wrote to look alike score lower against each other than against
> unrelated ones.
>
> Telling them apart means reading them.
>
> And I tested it honestly. Twenty reports, written before I tuned anything, run
> once at the end. Twenty out of twenty. It refused nothing in that run, so it
> does not prove it can turn one down.

---

## Clip 11 · Seedance D, the porch light

**14 seconds.** The closing shot, and the one the name is built on.

```
Slow push in on a suburban front porch at dusk, the house soft and out of focus
behind. Partway through the shot a porch light switches on, warm amber pooling
across the step, the door frame and a few feet of path. Everything else stays deep
blue evening. Nobody in frame. 50mm lens, shallow depth of field, very slow
deliberate push, no lens flare, no sparkle. Muted filmic palette, soft grain,
24fps cinematic, quiet and warm.
No text, no signage, no house numbers, no logos.
```

**Narration** *(24 words, 103 wpm)*

> Porchlight reads every report so nobody has to, and tells a street the one
> thing worth knowing.
>
> Which most weeks is nothing at all.

---

## Clip 12 · End card

**8 seconds.** Make it in CapCut: Georgia, Chalk `#E9EEF7` on Dusk `#0B1120`, the
repo URL and the live link. No motion.

**Narration** *(17 words, 128 wpm)*

> It is on GitHub, MIT licensed, and that report is live. Every report in it is
> invented.

---

## Two spare shots

Generate these only if a beat drags and needs a cutaway. Do not force them in.

```
Close overhead shot of a phone lying face down on a wooden kitchen table beside a
mug, its screen glowing faintly through the gap, then a hand slides it further
away. Warm late afternoon window light, 85mm macro, shallow depth of field.
Muted warm palette, soft grain, 24fps cinematic.
No readable text, no icons, no logos.
```

```
Wide static shot of an empty residential street at night. One warm streetlight,
parked cars, no people, nothing moving except leaves. Deep blue with a single warm
accent. 35mm, locked off, no camera movement. Muted, filmic grain, 24fps.
No text, no signage, no logos.
```

---

## CapCut assembly

**Project at 1920x1080, 30fps.** Generated clips usually arrive at 24fps and
screen recordings at 30 or 60. Set the project once and let CapCut conform
everything. Do not change it between sessions.

**Cut picture first, record narration against it.** The timings above assume the
cut exists. Recording voice to a stopwatch and building picture around it is how
videos end up forty seconds long.

**Colour.** Generated clips and screen recordings will not match out of the box.
Pull the generated shots toward the paper and dusk palette: lift the blacks
slightly, drop saturation, warm the highlights. **Do not grade the screen
recordings.** They are evidence.

**Sound.** Room tone or a very quiet pad underneath so the silences do not read
as dropouts. Nothing with a beat. The argument here is calm and music that pushes
will fight it.

**Transitions.** Hard cuts throughout. The one exception is clip 2 into clip 3,
where the animation has already gone to dusk, so a short dissolve reads as one
move rather than two.

**Before export.** Total under 5:00 with the end card included, and no generated
clip containing legible text.
