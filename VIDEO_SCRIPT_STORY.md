---
tags: [video, script, story, hackathon, porchlight]
status: draft
created: 2026-09-10
---

# Demo video, story cut

> An alternative to [[VIDEO_SCRIPT]], not a replacement. Same run, same footage,
> same five minute limit. What changes is the shape: this one is told as one
> story by one person, in first person, start to finish.
>
> [[VIDEO_SCRIPT]] stays the reference for production detail and it is the file
> `scripts/check_claims.py` reads. [[SHOOT_RUNBOOK]] still has the commands.

> [!warning] Nothing here is checked by the claims checker yet
> `check_claims.py` verifies the report quotes and the alert figures in
> [[VIDEO_SCRIPT]]. It does not know this file exists. Every number below was
> copied from the run of 2026-09-10 by hand, so if the run is ever repeated,
> either point the checker at this file too or read the numbers off the terminal
> again.

---

## The shape

Situation, complication, action, resolution. One person talking.

| | Beat | Roughly |
|---|---|---|
| 1 | The chat everybody muted | 0:00 to 0:50 |
| 2 | Who is supposed to catch it | 0:50 to 1:15 |
| 3 | What it does with thirty eight reports | 1:15 to 3:30 |
| 4 | How it works | 3:30 to 4:20 |
| 5 | Whether I believe it | 4:20 to 5:00 |

> [!danger] This full version is 1038 words and will not fit
> Counted 2026-09-10: **1038 words is 6:40 at 155 wpm and 7:40 at 135 wpm**,
> against a hard five minute limit. An earlier line here claimed about 660 words
> and was simply wrong.
>
> **Record from [[VIDEO_EDIT_PLAN]], not from this file.** It carries the same
> beats trimmed to **561 words across 4:52**, with each clip checked so that no
> line needs more than 135 words per minute. Keep this file for the argument and
> the order; take the words to say from the edit plan.

---

## 1 · The chat everybody muted

**On screen:** the four cluster reports, one at a time, as plain messages. No
amber anywhere in this beat.

**Narration** *(~150 words)*

> My street has a group chat. Yours probably does too.
>
> A pothole. The street light is out again. Someone has left the bins blocking
> the alley. Fireworks last night, waking the baby. It goes all day.
>
> So I muted it. Everyone I know has muted  it. And that's the problem, because
> that chat is also where you would find out if something was actually going on.
>
> Here are four messages. Four different people, over about a day and a half.

*(let them land, one at a time)*

> There has been a guy hanging around the mailboxes the last couple of evenings.
>
> Saw someone loitering by the post boxes again tonight when I got back from work.
>
> Somebody was messing about near where the packages get dropped when I left this morning.
>
> Person waiting around by the delivery lockers early on again.

> Same place, four times. Mailboxes. Post boxes. Where the packages get dropped.
> Delivery lockers. Not one word in common.
>
> Nobody in that chat is going to catch that. I wouldn't. You read them a day
> apart, on mute, and they are four separate bits of noise.

> [!danger] Read them exactly as written
> These are verbatim from `data/seed_reports.json` and the report page shows
> them again in §3 with their full text. Keep "a guy". It is the phrase that
> gets stripped later, and §3 pays it off.

---

## 2 · Who is supposed to catch it

**On screen:** the terminal, empty, waiting. Or a still of the group chat.

**Narration** *(~90 words)*

> The person who is meant to catch it is a volunteer. A block captain, somebody
> who moderates a local server, whoever ended up with the job. They are not paid
> for this and they already have too much on. The honest alternative to "someone
> reads every message" is that nobody does.
>
> So I wanted to know what an agent looks like if you measure it by how often it
> doesn't interrupt you.
>
> This is thirty eight reports going through it. Watch what mostly happens.

---

## 3 · What it does with thirty eight reports

**On screen:** the live run. See [[SHOOT_RUNBOOK]] for the command and the shot
order. The reasoning lands in a block at the end, so 3b and 3c are shot by
scrolling back up after it finishes.

### 3a · Nothing

**Narration** *(~45 words)*

> Nothing.
>
> Thirty seven of these never reach a single person. No alert, nobody notified,
> nobody woken up. That is not it failing to do its job. That is the job.

> [!warning] Say thirty seven of thirty eight and stop there
> The split between quietly logged and actively refused moves by one between
> runs. Both mean nobody hears about it. Only "38 in, 1 alert out" is fixed.

### 3b · The one it found and didn't send

**On screen:** the Birch Ln cluster in the reasoning block. Hold on it.
Evidence line reads `4 reports · 4 reporters · 504h · 1 zone(s) · z=1.2`.

**Narration** *(~130 words)*

> This is the part I actually care about. Something it found, and didn't send.
>
> Four reports. Four different people. One street. A van left running for
> twenty minutes. Someone looking into parked cars. A car going up and down the
> road near the driveways. A person wandering around near those same driveways.
>
> Four separate neighbours is real corroboration. Any threshold I could have
> written would have fired on that.
>
> Then look at the dates. Three weeks. The most recent one came twelve days
> after the one before it.
>
> Here is what it said about that:
>
> *"Four people each saw one thing, weeks apart, that looked a bit odd to them.
> That's a street, not a situation."*
>
> Declined. Nobody hears about it. Nobody gets talked about.

> [!tip] This is the twenty seconds the whole video rests on
> Let the reasoning sit on screen long enough to actually be read. It will feel
> too long to you, because you already know what it says. There is more than one
> refusal in the run. Use one.

### 3c · The one it sent

**On screen:** the pattern block and the alert firing, then the approval prompt,
then the fourth report of the same cluster being held back.

**Narration** *(~140 words)*

> And then this one.
>
> Three reports. Three different people. One zone. Thirteen hours. And a rate of
> reporting that street does not normally see.
>
> That is the cluster from the beginning. The four that share no words. It found
> them by meaning, counted how many separate people had filed them, and decided
> this one was worth interrupting somebody for.
>
> It doesn't send it though. It drafts it and asks. A person still has to say
> yes, and that matters more than it sounds, because this goes out to everyone
> on the street, and the person being described is probably one of them.

*(type y)*

> Then a fourth report comes in about the same place. It doesn't alert again.
> That situation is already open and the street has already been told.
>
> One alert. Out of thirty eight.

> [!warning] The numbers are 3 / 3 / 13 hours
> It fires on the third report, not the fourth. The four report, thirty six hour
> state belongs to the one that gets held back. Read them off your own terminal.

### 3d · What it kept

**On screen:** the two column section of the report page. There is a Replay
button, so you can take this as many times as you like.

**Narration** *(~110 words)*

> Now look at what it kept.
>
> On the left, what people actually typed. On the right, what Porchlight stored.
>
> The one at the top is a broken locker door. Same street as the cluster. Logged,
> and nobody hears about it.
>
> Then those four. Four people, four ways of describing it, no word in common,
> and one place.
>
> And every description of a person is gone. "A guy" came out as "a person".
> That is not the prompt being polite about it. It is enforced in code, with a
> retry, before the text ever reaches the database.
>
> What the alert gives you is a place to watch. Never a person to look for.

> [!warning] Say the same place, not the same sentence
> It is six rows, and the right hand column is four different sentences. What
> they share is the place. The page counts it for you underneath.

---

## 4 · How it works

**On screen:** `assets/architecture.html`, held.

**Narration** *(~135 words)*

> Three agents, in order, built with the Strands Agents SDK on Bedrock.
>
> Haiku reads one report, works out what kind of thing it is, and rewrites it as
> a single neutral sentence with the person taken out. That sentence is the only
> copy that lasts.
>
> Sonnet searches everything stored so far and works out which reports describe
> the same situation. It gives back which ones, and why it thinks so. It never
> gives back a count.
>
> The counting is code. How many reports, how many separate people, over how
> long, and how unusual that is for that particular street. A number the model
> reports about itself isn't a safety control.
>
> Opus takes all of that and decides. There is no "if more than three reports"
> anywhere in this. Every decision it makes carries its reasoning, which is what
> you have been reading this whole time.

---

## 5 · Whether I believe it

**On screen:** the graph, held. Then the holdout result.

**Narration** *(~155 words)*

> I did check whether a plain similarity score could do this instead of an
> agent. It can't. Three reports I wrote to look alike score lower against each
> other than one of them scores against a totally unrelated report about a car
> passing some driveways.
>
> Telling those two situations apart means reading them. That is the argument
> for putting an agent here.
>
> And I tried to test it honestly. Twenty reports, written before I tuned
> anything, held back, run once at the end. Twenty out of twenty. It found a
> bike theft that nobody described the same way, and it stayed quiet on four
> reports that all say "parked car on Sycamore Row" and have nothing to do with
> each other.
>
> What it didn't do in that run is refuse anything. So it shows me it can find a
> hard pattern. It doesn't show me it can turn down one that looks real.
>
> Small scale community safety runs on volunteers with no tools at all.
> Porchlight reads every report so that nobody has to, and tells a street the one
> thing worth knowing. Which most weeks is nothing.

---

## Close

**On screen:** repo URL and the live link.

> It's on GitHub under an MIT licence, and the report you just watched it
> generate is live at that link.
>
> Every report in it is invented. There are no real users and no real incidents.
> The page says so too.

---

## Things not to say

- Anything with "spidey", costume red, or a Marvel reference in it. The phrase
  "friendly neighborhood" on its own is fine. See [[BRANDING]].
- The near miss "declined on the spread". It never gets assembled, so it never
  gets refused. The Birch Ln cluster in §3b is a different thing and it is real.
- The holdout without its limit. It produced no refusals, so it does not show
  the agent turning down a plausible cluster. That sentence is in §5 and stays.
- The split between logged and refused. Thirty seven of thirty eight.
- Anything about real users, real deployments, or real incidents. There are none.

## Notes on delivery

Record the screen silent and do this separately, over the top. If you fluff a
line you redo the line, not the run.

Read it like you are telling somebody about it, not like you are reading it.
The bits that will sound written are §4 and the first half of §5, so slow down
there and let yourself stumble slightly. It is better than sounding polished.

Nowhere in this needs you on camera.
