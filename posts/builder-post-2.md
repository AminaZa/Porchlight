---
tags:
  - hackathon
  - porchlight
  - builder-post
status: published
created: 2026-08-21
target: builder.aws.com
published: 2026-08-22
url: https://builder.aws.com/content/3IH3gxMX7EiBVvcj8LNeOrinhXc/the-wrong-pair-ranks-higher-than-the-right-pair-why-my-agents-for-humans-build-needed-an-agent
---

# Post 2 — why a threshold can't do this

> **PUBLISHED 2026-08-22.** Bonus scoring: 0.2 of a possible 0.6, and it only counts if it is
> **published** on builder.aws.com before 14 Sep 2026, 5pm PT.
> Title must contain the phrase *Agents for Humans*.
>
> **builder.aws.com caps a post at 3000 characters.** Everything below the rule
> is the post; keep it under the cap. Run `python scripts/postlen.py` to check.
> The longer draft this was cut from is in git history at commit `ba17e4f`.

**Title:** The Wrong Pair Ranks Higher Than the Right Pair: Why My Agents for Humans Build Needed an Agent

**Summary** *(article description field, 288 chars)*: Why my neighbourhood safety agent needs an agent. The near-miss reports in my dataset resemble each other less than one of them resembles a completely unrelated report — the ordering is inverted, so no cosine threshold separates them at any value. The deciding evidence isn't in the text.

**Summary, short** *(if the field is tighter, 155 chars)*: The near-miss reports resemble each other less than one resembles an unrelated report. The ordering is inverted, so no cosine threshold works at any value.

**Tags:** `agents-for-humans` `strands-agents` `amazon-bedrock` `rag` `embeddings`

---

In [my last post](https://builder.aws.com/content/3IH3FtgK3xtZL4ft7oUrPtvLPpu/redaction-made-my-retrieval-work-a-measurement-from-an-agents-for-humans-build) I fixed retrieval in a neighbourhood safety agent by indexing a normalised summary instead of raw report text: group separation went from −0.16 to +0.52.

That invites an obvious question, and I spent a day trying to make the answer be yes.

If retrieval separates the groups that cleanly, why is there an agent here at all? Cluster on cosine similarity, pick a threshold, alert above it. An afternoon of work, nothing to tune, no model to pay for.

I measured it. It does not work, and *how* it fails is the interesting part.

**The case that decides it.** My dataset contains a deliberate near-miss: three reports of someone loitering, in **three different zones**, spread over **three weeks**. It should not alert — that is roughly the base rate of living somewhere, and broadcasting it is what teaches people to mute the service.

Next to it sits a genuine cluster: four reports, one parcel locker, 36 hours, four separate reporters. That one should alert.

In plain language both are "several people reported someone hanging around."

| | cosine similarity |
|---|---|
| Within the genuine cluster | 0.708 – 0.814 |
| **Within the near-miss** | **0.436 – 0.456** |
| **Near-miss report → an unrelated report** | **0.576** |

Read the last two rows again. The near-miss reports resemble **each other less** than one of them resembles an unrelated report about a car driving past some driveways.

This is not a threshold that needs tuning. The **ordering is inverted**. Sort every pair by similarity and the wrong pair sits above the right pair. No cut point puts one on the correct side without putting the other on the wrong side. Tuning changes which mistakes you make, not whether you make them.

I swept it anyway. To assemble the near-miss group at all you have to drop to 0.45, and you buy that with 20 wrong cross-group links; 0.40 catches it properly and costs 60. At 0.50 and up the noise clears and the near-miss group is simply invisible — never assembled, so never declined. Ten to one against, at every setting.

**What actually separates them is not in the text.** One place versus three zones. 36 hours versus three weeks. Four independent reporters versus three strangers. Similarity cannot see any of it.

You could bolt on `if same_zone and span < 48h and reporters >= 3`. It gets both my cases right; I ran it. But every constant there is a guess dressed as a policy, and — more importantly — it cannot explain itself. When my agent declines it says *why*, in a sentence a neighbour can read and argue with. `span < 48` returning False is not a reason. For a system whose whole value is staying quiet, the account of why it stayed quiet is what earns it the right to keep running.

Open source, MIT: **https://github.com/AminaZa/Porchlight**


