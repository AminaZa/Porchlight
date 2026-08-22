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
>
> **builder.aws.com caps a post at 3000 characters.** Everything below the rule
> is the post; keep it under the cap. Run `python scripts/postlen.py` to check.
> The longer draft this was cut from is in git history at commit `ba17e4f`.

**Title:** Redaction Made My Retrieval Work: A Measurement From an Agents for Humans Build

**Tags:** `agents-for-humans` `strands-agents` `amazon-bedrock` `rag` `privacy`

---

I am building a neighbourhood safety agent for the AWS *Agents for Humans* hackathon. It reads reports from neighbours and wakes a human only when several people independently describe the same situation in the same place. On the demo set, 37 of 38 reports never surface. One alert fires.

The whole thing rests on one premise: four people describing the same event in different words still land near each other in embedding space. I checked that before building on it.

It failed.

**The cluster it has to find.** Four neighbours, one parcel locker, 36 hours:

> a person hanging around the **mailboxes**
> someone loitering by the **post boxes**
> messing about near **where the packages get dropped**
> waiting around by the **delivery lockers**

No shared content word. That is why keyword matching cannot do this.

**What happened.** I indexed the raw report text. The weakest cluster report ranked *below an unrelated report*. Separation came out at **−0.03 to −0.16** across every query strategy I tried.

Negative. Confidently wrong, in the exact case the product exists for.

The cause was in the strings. These reports are short, and most of each one is narration — *"when I got back from work," "again tonight," "probably nothing but."* Two neighbours who both mention their commute look more alike, to a 384-dimensional embedding of forty words, than two who saw the same person at the same lockers. The signal was about six words. The noise was everything else, and the noise was shared.

**The fix.** The pipeline already had a triage stage that strips person-identifying detail before anything is stored — height, clothing, ethnicity, vehicle, name. That was there for privacy, and I carried it as a cost: a thing I do because I should, which presumably makes the downstream job harder by throwing information away.

I indexed the normalised triage summary instead of the raw text.

The same groups separated by **+0.28 to +0.52**. Cluster matches landed at 0.69–0.77; unrelated reports topped out at 0.32. Same embedding model, same dimensions, same query code. The only thing that changed was which string went in.

Redaction was not a tax on accuracy. Redaction is **what makes retrieval work**. The operation that removes the person also removes the commute, the weather, and the apology for bothering anyone — and what is left is the incident.

Two things I would take from it:

**For short texts, what you index is a bigger lever than which model embeds it.** A swing from −0.16 to +0.52, no model change.

**Check whether your privacy step is actually a cost.** I assumed it traded accuracy for compliance, because that is the shape those tradeoffs usually have. It was the largest accuracy gain in the project.

Open source, MIT: **https://github.com/AminaZa/Porchlight**

Next: why a cosine threshold at *any* value cannot tell the real cluster from a near-miss.
