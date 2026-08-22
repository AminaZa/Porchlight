---
tags: [submission, devpost, hackathon, porchlight]
status: draft
created: 2026-08-20
---

# Devpost submission copy

> Paste-ready text for the Devpost form. Field names below match the form's own
> sections. Companion to [[VIDEO_SCRIPT]] and [[CHECKLIST]] §4.
>
> **Track:** Good Neighbor Agents

> [!warning] Three things here are not true yet
> Marked `⟨PENDING⟩` inline. All three depend on the first real (non-offline)
> run — do not submit with them unresolved, and do not soften them into
> something vaguer to avoid the wait. Either the number is real or the sentence
> comes out.

---

## Project name

```
Porchlight
```

## Elevator pitch

*Devpost caps this around 200 characters. First one is the recommendation.*

```
A neighborhood safety agent defined by how often it stays quiet. It reads every report, correlates by meaning rather than keyword, and wakes a human only when several neighbors independently describe the same thing.
```

Alternates, if the field runs short:

```
Reads every neighborhood safety report, correlates them by meaning, and wakes a human only for the ones that turn out to be a real pattern. On the demo set, 37 of 38 never surface; one alert fires.
```

```
Your friendly neighborhood agent. Three Strands agents that read every report, find the real patterns, and stay quiet the rest of the time.
```

---

## About the project

### Inspiration

Neighborhoods already report things to each other — a missing package, someone
loitering near the mailboxes, a car circling the block. It lands in a Discord
server, a WhatsApp group, an HOA email chain.

Three things go wrong. Every report is treated identically, so a one-off and the
third theft on the same street this week produce the same notification. Nobody
correlates, because the pattern is only visible if one person reads every message
and remembers them all — and that person doesn't exist, or burns out. And the
wording varies wildly, so keyword matching misses the cases that matter most.

The starting question was: what does an agent look like if its value is measured
by how often it *doesn't* interrupt you?

### What it does

Porchlight reads every report a neighborhood submits, works out which ones
describe the same ongoing situation, and wakes a human only when the evidence
supports it. On the demonstration dataset, **thirty-seven of thirty-eight reports
never surface to anyone. One alert fires.**

The problem it's built around looks like this. Four neighbors notice the same
person near the same parcel lockers over a day and a half, and report it as:

- "a person hanging around the **mailboxes**"
- "someone loitering by the **post boxes**"
- "somebody messing about near **where the packages get dropped**"
- "a person waiting around by the **delivery lockers**"

**Those four reports share no content word.** Any keyword filter sees four
unrelated notes. A moderator reading them a day apart sees four unrelated notes.

Three behaviors are worth watching:

| | Evidence | Outcome |
|---|---|---|
| The real cluster | 4 reports · **4 different reporters** · one zone · 36 hours | **Alert** |
| The near-miss | 3 similar reports · 3 reporters · **three zones** · **21 days** | Declined |
| The single reporter | 4 similar reports · one zone · 3.5 days · **1 reporter** | Declined |

The second and third rows are the point. A system that only ever fires isn't
exercising judgment — the declines are what make the alert worth reading. The
third is also a safety control: four reports from one person isn't corroboration,
and treating it as a neighborhood pattern is how a service like this gets used
against somebody.

### Who it's for

Everyone on the street. Alerts go to the residents of the affected zone, so the
people the product is for are the neighbours who currently get pinged for every
raccoon and every strange car, and who have quietly muted the channel because of
it. The thing Porchlight gives them is the silence — thirty-seven of thirty-eight
reports never reach them at all, which is what makes the thirty-eighth worth
opening.

The volunteer who runs the channel — a block captain, an HOA coordinator, a
moderator for a local server — is still in this, but not as the customer. They
are the human in the loop: the agent reads everything and drafts, and a person
approves before anything is broadcast. Unpaid and already stretched, which is
exactly why the reading is the part worth automating.

Small-scale community safety is almost entirely volunteer-run and unsupported by
tooling. The realistic alternative to "someone reads every message" is nothing at
all.

### How we built it

Three Strands agents run as a sequential workflow, each on the smallest model
that can do its job.

**Triage** (Claude Haiku 4.5) classifies one report and rewrites it as a single
neutral sentence with every person-identifying detail removed. That sentence is
the only long-lived copy — the reporter's original words are held briefly, never
indexed, and deleted on a retention timer.

**Correlation** (Claude Sonnet 5) has three tools: semantic search over past
reports, a per-zone anomaly check, and zone history. It decides which reports
describe the same situation and explains its reading of the evidence. It returns
IDs and prose — never counts.

**The pipeline counts the evidence** from storage: how many reports, how many
*distinct* reporters, over what time span, across how many zones, and how unusual
that rate is for that particular place.

**Escalation** (Claude Opus 5) weighs that and decides. The decision lives in the
agent's reasoning under its system prompt, never in an `if count > 3` branch, and
every decision carries a required `reasoning` field shown on screen.

Retrieval is ChromaDB with local ONNX embeddings — no API key, no per-embedding
cost, deterministic across runs. The report log is SQLite. Anomaly detection
models each zone's arrival rate against its own history as a Poisson process, so
a busy through-road and a quiet courtyard are held to different baselines.

**Built with:** Strands Agents SDK · Amazon Bedrock · Claude Haiku 4.5 / Sonnet 5
/ Opus 5 · ChromaDB · SQLite · numpy · scipy · Pydantic · Python 3.12

### Challenges we ran into

**Indexing the raw report text does not work,** and finding that out changed the
design. On the first run of the premise check, the weakest cluster report ranked
*below* an unrelated one — separation of −0.03 to −0.16 across every query
strategy we tried. Incidental narration ("when I got back from work", "again
tonight") dominates the embedding of a short text. Indexing the normalized triage
sentence instead separates the same groups by +0.28 to +0.52.

That turned the privacy decision and the accuracy decision into the same
decision. Redaction isn't a tax paid against retrieval quality — it's what makes
retrieval work.

**Most of the real defects came from looking, not from testing.** A four-report
cluster rendering as three nodes. The terminal printing ALERT next to a tally
counting it as suppressed. Nothing suppressing repeat alerts, so every later
report joining an escalated cluster would alert again. The suite is what stops
them coming back; it isn't what found them.

### Accomplishments that we're proud of

**We measured whether a cheaper design would work, and published the answer.**
The obvious alternative is to embed everything and call it a cluster above some
similarity threshold. On our data it fails:

| | cosine similarity |
|---|---|
| Within the genuine cluster | 0.708 – 0.814 |
| **Within the near-miss** | **0.436 – 0.456** |
| **Near-miss report → an unrelated report** | **0.576** |

The near-miss reports resemble each other *less* than one of them resembles a
completely unrelated report about a car driving past some driveways. Sweeping the
threshold doesn't rescue it — at 0.45 it finds two correct links and twenty
incorrect ones; at 0.50 and above, none at all. Separating "three people
described loitering in three zones over three weeks" from "these two sentences
both mention driveways" requires reading them. That is the argument for putting
an agent here, and it's measured rather than asserted.

**Redaction is enforced, not requested.** A Strands `AfterModelCallEvent` hook
inspects what the model actually produced — including the structured-output
fields — and if a summary still describes a person, sets the event's `retry`
flag: the response is discarded and regenerated before the pipeline, storage, or
the index ever sees it. A prompt is an instruction; this is a control.

**A holdout set, written before any tuning.** Twenty reports we never looked at
while tuning prompts, including two adversarial cases: a real cluster whose
reporters share almost no vocabulary, and four same-street reports that are four
unrelated incidents. Run once, at the end. ⟨PENDING — result goes here and in the
README, whatever it is⟩

### What we learned

That the interesting engineering in an agent product is often in the *declining*.
Getting Porchlight to find the cluster took an afternoon. Getting it to reliably
not fire on the near-miss — and to explain why in a way a volunteer coordinator
would find reasonable — was the real work.

Also that safety architecture and product quality kept turning out to be the same
thing. Correlating on place and behavior instead of person descriptions is a
bias mitigation *and* what makes retrieval work. Requiring distinct reporters is
a harassment defense *and* a correctness fix.

### What's next

Consent flow for reporters. A moderation queue. Real alert dispatch over SMS or
Discord. Per-reporter rate limiting and a false-report path. Deployment to
AgentCore Runtime. The structural safety work is already in, so these are
additive rather than a rewrite.

Before real residents use it, the README says plainly that we'd need advice on
liability if an alert precedes a confrontation, and on whether the operator
becomes a data controller under the applicable privacy regime. That's not a
footnote we want to discover after launch.

---

## Other form fields

**Try it out links**
```
https://github.com/AminaZa/Porchlight
```
⟨PENDING — S3 live demo URL, after a real run + ./scripts/publish.sh⟩

**Built with** *(tag list)*
```
strands-agents, amazon-bedrock, claude, python, chromadb, sqlite, numpy, scipy, pydantic, opentelemetry
```

**Video** — ⟨PENDING — public YouTube or Vimeo URL⟩

**AWS Builder ID** — ⟨PENDING — account created 2026-08-21; paste the ID itself here⟩

**Bonus: builder.aws.com posts** — all three published 2026-08-22, 0.2 each.
The rules require these to be *submitted*, not merely published: "Submitting the
following optional builder.aws Blog Post will positively impact the score"
(§ Project Requirements). Paste all three URLs wherever the Devpost form asks
for them.

1. https://builder.aws.com/content/3IH3FtgK3xtZL4ft7oUrPtvLPpu/redaction-made-my-retrieval-work-a-measurement-from-an-agents-for-humans-build
2. https://builder.aws.com/content/3IH3gxMX7EiBVvcj8LNeOrinhXc/the-wrong-pair-ranks-higher-than-the-right-pair-why-my-agents-for-humans-build-needed-an-agent
3. https://builder.aws.com/content/3IH4JGX8muNHBXdCNGDDRgpAbeu/a-prompt-is-not-a-control-enforcing-a-safety-guarantee-with-a-strands-hook-in-an-agents-for-humans-build

---

## Pre-submit checks

- [ ] Every `⟨PENDING⟩` above resolved or removed
- [ ] Demo numbers re-checked against the first real run, not the offline one
- [x] No Marvel references anywhere — see [[BRANDING]] § *Trademark scope* ✅ 2026-08-22
- [ ] Repo public, MIT license visible in the About section
- [ ] Video public on YouTube or Vimeo, under 5:00
- [ ] Submitted before **Sep 14, 2026 5:00pm PT**
