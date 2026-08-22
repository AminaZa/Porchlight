---
tags: [hackathon, porchlight, builder-post]
status: published
created: 2026-08-21
target: builder.aws.com
---

# Post 2 — why a threshold can't do this

> Draft. Bonus scoring: 0.2 of a possible 0.6, and it only counts if it is
> **published** on builder.aws.com before 14 Sep 2026, 5pm PT.
> Title must contain the phrase *Agents for Humans*.

**Title:** The Wrong Pair Ranks Higher Than the Right Pair: Why My Agents for Humans Build Needed an Agent

**Tags:** `agents-for-humans` `strands-agents` `amazon-bedrock` `rag` `embeddings`

---

In [my last post](⟨PENDING — URL of post 1, after it is published⟩) I wrote about fixing retrieval in a neighbourhood safety agent — indexing a normalised summary instead of raw report text, which took group separation from −0.16 to +0.52.

That fix invites an obvious question, and I want to answer it honestly, because I asked it myself and spent a day trying to make the answer be yes.

If retrieval separates the groups that cleanly now, why is there an agent here at all? Cluster on cosine similarity, pick a threshold, alert above it. That is an afternoon of work, it costs nothing to run, and it has no prompt to tune and no model to pay for.

I measured it. It does not work, and the way it fails is more interesting than the fact that it fails.

## The case that decides it

My dataset contains a deliberate trap I call the near-miss. Three reports of someone loitering — in **three different zones**, spread over **three weeks**, from three different neighbours.

It should not alert. Nothing is happening. Three people in three parts of a neighbourhood noticed something vaguely unsettling over most of a month, which is roughly the base rate of living somewhere. Broadcasting that to a neighbourhood is exactly the behaviour that teaches people to mute the service.

It sits in the data next to a genuine cluster: four reports, one parcel locker, thirty-six hours, four separate reporters. That one should alert.

Both groups are, in plain language, "several people reported someone hanging around." A system that cannot tell them apart is either useless or harmful, depending on which way it errs.

## The numbers

| | cosine similarity |
|---|---|
| Within the genuine cluster | 0.708 – 0.814 |
| **Within the near-miss** | **0.436 – 0.456** |
| **A near-miss report → an unrelated report** | **0.576** |

Read the last two rows again, because that is the whole post.

The near-miss reports resemble **each other less** than one of them resembles a completely unrelated report about a car driving past some driveways.

This is not a threshold that needs tuning. The *ordering is inverted*. Sort every pair in my dataset by similarity and the wrong pair appears above the right pair. There is no cut point anywhere on that sorted list that puts one on the correct side without putting the other on the wrong side, because they are in the wrong order to begin with. Tuning changes which mistakes you make, not whether you make them.

## The sweep, for completeness

I did not want to argue this from three numbers, so I swept the threshold across the full dataset and counted what any similarity-clustering approach would actually link:

| threshold | correct near-miss links | wrong cross-group links |
|---|---|---|
| 0.40 | 6 | 60 |
| 0.45 | 2 | 20 |
| 0.50+ | 0 | — |

To retrieve the near-miss group as a group at all — which you must do before you can decide it is not worth alerting on — you have to drop to 0.45, and you buy that with twenty wrong links. Drop to 0.40 to catch it properly and you are carrying sixty. Go to 0.50 and up, where the cross-group noise finally clears, and the near-miss group is simply invisible: the system never assembles it, so it never gets the chance to decline it.

Ten to one against, at every setting. There is no window.

## So what actually separates them?

Nothing in the text. The distinguishing evidence is entirely outside it:

- **Where** — one place, versus three zones spread across the neighbourhood
- **When** — thirty-six hours, versus three weeks
- **Who** — four independent reporters, versus three people who have never encountered each other

Similarity cannot see any of that. It is metadata, and it is the whole case.

## "Then add rules on top of the threshold"

This is the fair counter-argument and it deserves a real answer, not a strawman. You could write:

```python
if same_zone and span_hours < 48 and distinct_reporters >= 3:
    alert()
```

That rule gets both of my cases right. I ran it.

Two problems, and the second one is why I stopped.

**It is brittle in the way hand-tuned constants always are.** Why 48 hours? Because it fits the case in front of me. A genuine pattern spread over sixty hours falls out. Two zones that happen to share a boundary — a parcel locker on the line between them — falls out. Every one of those constants is a guess dressed up as a policy, and each new case adds another clause.

**It cannot explain itself, and explanation is the product.** When Porchlight declines, it says why: *"three reports, but in three different zones over three weeks — the resemblance between them is not evidence that they are connected."* A neighbour can read that, disagree with it, and tell me it is wrong. `span_hours < 48` returning `False` is not a reason anyone can argue with. In a system whose entire value proposition is that it stays quiet, the account of *why* it stayed quiet is the thing that earns it the right to keep running.

So the escalation stage is a model that reads the evidence — the cluster, the reporter count, the time span, the zone spread, the anomaly score — and weighs them against each other for the specific case, then writes its reasoning in plain language. Not because agents are fashionable. Because the decision genuinely requires reading, and because the output has to be a sentence a human can push back on.

## One consequence worth flagging

My demo has an `--offline` mode so it can run with no AWS account and no spend — the three model calls are stubbed, everything else is real.

Offline mode **cannot** reproduce the near-miss decline. I documented that loudly rather than papering over it, because it follows directly from everything above: the judgment is the part that was stubbed, and a stub with no judgment cannot demonstrate judgment. If I could fake that decline with a hard-coded rule, the argument in this post would be wrong.

The build is open source under MIT: **https://github.com/AminaZa/Porchlight**

Post 3 will be about enforcing a safety guarantee — "no alert ever describes a person" — with a Strands hook on the model call, rather than asking the prompt nicely and hoping.
