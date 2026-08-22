---
tags: [hackathon, porchlight, builder-post]
status: draft
created: 2026-08-21
target: builder.aws.com
---

# Post 1 — the retrieval failure

> Draft. Bonus scoring: 0.2 of a possible 0.6, and it only counts if it is
> **published** on builder.aws.com before 14 Sep 2026, 5pm PT.
> Title must contain the phrase *Agents for Humans*.

**Title:** Redaction Made My Retrieval Work: A Measurement From an Agents for Humans Build

**Tags:** `agents-for-humans` `strands-agents` `amazon-bedrock` `rag` `privacy`

---

I am building a neighbourhood safety agent for the AWS *Agents for Humans* hackathon. It reads incident reports from neighbours and wakes a human only when several different people have independently described the same situation in the same place over a short window. On the demo dataset, thirty-seven of thirty-eight reports never surface to anyone. One alert fires.

The whole system rests on one premise: that four people describing the same thing in completely different words will still land near each other in embedding space. So before building anything on top of it, I wrote a check for exactly that.

It failed.

## The four reports

Here is the cluster the system is supposed to find. Four neighbours, one parcel locker, thirty-six hours:

> "There has been a person hanging around the **mailboxes** the last couple of evenings."
>
> "Saw someone loitering by the **post boxes** again tonight when I got back from work."
>
> "Somebody was messing about near **where the packages get dropped** when I left this morning."
>
> "A person was waiting around by the **delivery lockers** early on again."

Those four share no content word at all. That is the point — it is why keyword matching cannot do this, and why I expected embeddings to earn their place.

## What actually happened

I indexed the raw report text and queried it. The weakest of the four cluster reports ranked **below an unrelated report**. Separation came out between **−0.03 and −0.16** across every query strategy I tried, including querying with a report's own text.

Negative separation. The retrieval was worse than useless — it was confidently wrong, in the one case the entire product exists to handle.

The cause, once I looked at what was actually in the strings: these are short texts, and a large fraction of each one is incidental narration. *"when I got back from work."* *"again tonight."* *"probably nothing but."* Two neighbours who both mention their commute look more alike, to a 384-dimensional embedding of forty words, than two neighbours who both saw the same person at the same lockers.

The signal was maybe six words per report. The noise was everything else, and the noise was shared.

## The fix, and why it surprised me

The pipeline already had a triage stage in front of retrieval — a small model that classifies each report and, separately, strips person-identifying detail before anything is stored. Height, clothing, ethnicity, vehicle, name. That was there for a privacy requirement, and I had been carrying it as a cost: a thing I do because I should, which presumably makes the downstream job a little harder by throwing information away.

I tried indexing the normalised triage summary instead of the raw text.

The same groups separated by **+0.28 to +0.52**. Cluster matches landed at 0.69–0.77; unrelated reports topped out at 0.32.

Redaction was not a tax on accuracy. Redaction was **what makes retrieval work**. The same operation that removes the person also removes the commute, the weather, the hedging, and the apology for bothering anyone — and what is left is the incident.

So I merged the two fields. There is no separate `summary` and `redacted_text` any more; there is one normalised sentence that is both. That also means there is exactly one redaction surface to defend instead of two, which is a much easier thing to test and a much easier thing to reason about.

## The trap it opens

Normalise hard enough and everything starts to look alike. If "person near lockers, evening" is the representation, then a genuine cluster and a coincidence collapse into the same point, and the system alerts on noise — which is the failure mode it was built to avoid.

My dataset has a deliberate near-miss in it: three reports of loitering, in three different zones, spread over three weeks. It should *not* alert. Those reports are semantically close to the real cluster, and if my normalisation ever gets too aggressive they will merge into it.

So the margin is a test, not a hope:

```python
def test_near_miss_stays_separable():
    # near-miss group must stay distinct from the genuine cluster
    assert margin > 0.20     # currently +0.284
```

A future prompt edit that quietly over-normalises now breaks the build instead of breaking the demo.

## What I would take from this

Three things, in the order they cost me time.

**Check your premise against your data before you build on it.** This check took an afternoon and it invalidated my indexing strategy. Had I written it after the retrieval layer, the correlation layer and the escalation layer were done, I would have been debugging a "the agent is bad at correlating" problem that was never in the agent.

**For short texts, what you index is a bigger lever than which model you embed with.** I never changed the embedding model. Same model, same dimensions, same query code — a swing from −0.16 to +0.52 came entirely from changing what string went in.

**Check whether your privacy step is actually a cost.** I assumed redaction traded accuracy for compliance, because that is the shape those tradeoffs usually have. Here it was the single largest accuracy improvement in the project. Worth measuring before you assume which way it points.

The build is open source under MIT: **https://github.com/AminaZa/Porchlight**

Post 2 will cover the other half of this — why a cosine-similarity threshold, at *any* value, cannot tell the genuine cluster from the near-miss, and why that is the argument for putting an agent here at all. I have the sweep numbers for that one and they are worse than you would guess.
