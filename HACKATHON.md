---
tags: [hackathon, requirements, porchlight]
status: active
created: 2026-08-20
source: REQUIREMENTS.md (full official rules — read that for legal text)
---

# Hackathon spec — AWS "Agents for Humans"

> Distilled from [[REQUIREMENTS]] for Claude Code. This is the operative summary: every
> requirement that changes what we build or ship. Companion to [[PROJECT_BRIEF]] (what/why),
> [[IMPLEMENTATION_PLAN]] (how) and [[CHECKLIST]] (what's left).

---

## 1 · Dates — the numbers that actually constrain us

| Event | When |
|---|---|
| Submission period | Aug 10, 2026 9:00 am PT → **Sep 14, 2026 5:00 pm PT** |
| AWS credit request deadline | **Sep 11, 2026 12:00 pm PT** ($50, while supplies last) |
| Judging | Sep 15 – Oct 8, 2026 |
| Winners announced | ~Oct 14, 2026, 2:00 pm PT |

**This resolves the open question in [[CHECKLIST]] §5.** The brief's "six weeks from project
start" is *not* six weeks from now. As of 2026-08-20 there are **25 days** to the deadline, and
the credits form closes 3 days before that. The brief's week-by-week plan should be read as a
priority ordering, not a calendar.

Drafts can be saved and edited freely until the deadline; after it, **no changes at all** to the
submission.

---

## 2 · Non-negotiables (Stage One is pass/fail on these)

1. **Built with the Strands Agents SDK.** Not incidental use — the agent must be a Strands agent.
2. **Newly created during the submission period** (Aug 10 – Sep 14, 2026). Any pre-existing code
   incorporated must be **disclosed**. AI coding assistants, frameworks, libraries and starter
   templates are explicitly allowed and need no disclosure.
3. **Does real work end to end — not a chatbot about the work.** The rules say this twice, in
   those words. It is the theme, not a nicety.
4. **Fits the theme:** runs autonomously in the background, surfaces only when a human decision
   is genuinely needed.
5. Original work, solely owned, no third-party IP violations. Third-party APIs/SDKs must be used
   within their licence terms.

A project that fails Stage One is never scored. Everything in §4 below is worth zero without these.

---

## 3 · Submission deliverables — the literal list

- [ ] **Text description** — what it does, who it's for, how it works
- [ ] **PUBLIC repo URL** (GitHub/GitLab/Bitbucket) with *all* source, assets and setup
      instructions needed to run it
- [ ] **MIT or Apache licence**, as a licence file, **detectable and visible in the repo's About
      section** — the rules specify the About section, not just a `LICENSE` file
- [ ] **README**
- [ ] **Architecture diagram**
- [ ] **Demo video, max 5 minutes**, public on **YouTube or Vimeo**, that both
      **demonstrates the working project** and pitches (1) the problem (2) who it's for
      (3) why it matters. Slides / screen recording / voiceover all fine; no need to be on camera.
- [ ] **AWS Builder ID**
- [ ] Optional but explicitly scores higher on Technical Implementation: **live demo link**
- [ ] All materials in English

**Testing clause:** judges must be able to access a working project free of charge and without
restriction until judging ends (Oct 8). If anything is gated, credentials go in the testing
instructions. Judges are *not obliged* to run it — they may score from the description, images
and video alone. **Treat the video and README as the primary artefacts.**

Track to enter: **Good Neighbor Agents** (agents that help groups, not one person) — matches
Porchlight exactly. One prize per project.

---

## 4 · Judging criteria — five, equally weighted

Each is worth the same. A project that is excellent at one and weak at another scores worse than
one that is solid at all five.

| # | Criterion | What it actually asks | Where Porchlight stands |
|---|---|---|---|
| 1 | **Technical Implementation** | How thoroughly and skilfully is Strands used? Non-trivial, working code, genuine effort. Live demo and/or **AgentCore deployment strengthen this**. | Three-agent Strands pipeline + four tool modules is the strong suit. Missing: live demo link, AgentCore. |
| 2 | **Design** | A complete, coherent *product* — not a proof of concept. | Branding, renderer, CLI, offline mode all feed this. |
| 3 | **Potential Impact** | A credible, *specific* case for a real problem and real audience — and does the demo show the solution actually addressing it? | The volunteer coordinator framing + the holdout result. |
| 4 | **Creativity & Originality** | Non-obvious use of Strands, plus demonstrated understanding of the problem space. | Semantic + statistical dual signal; LLM-held escalation judgment rather than a threshold. |
| 5 | **Presentation** | Does the video clearly show it working end to end? Is the pitch clear? Is it easy to follow? | Not started. Equal weight to all the engineering. |

**Ties** are broken by criterion order: Technical Implementation first, then Design, then Impact,
then Creativity, then Presentation.

### Bonus points
Up to **+0.6** for publishing build-journey posts on **builder.aws.com** (0.2 each, up to three),
publicly published **before the deadline**, covering the build and use of AWS. Final scores run
1 → 5.6.

> **Correction to carry into [[PROJECT_BRIEF]] §10 and [[CHECKLIST]] §4:** the rules were updated
> 2026-08-12 to **remove the `#AgentsforHumans` hashtag requirement**. The title should still
> *use the phrase* "Agents for Humans"; the hashtag is no longer required. Both our docs still
> say `#AgentsforHumans`.

0.6 points is a meaningful fraction of a 5-point scale for roughly an evening of writing. Three
posts is the maximum-value play, one is the minimum sensible one.

---

## 5 · What this means for the remaining 25 days

Reading the criteria against [[CHECKLIST]]:

**Presentation is 20% of the score and is entirely unstarted.** It carries the same weight as the
whole Strands implementation. The brief already flags "video left too late" as a recurring cause
of weak submissions; the compressed timeline makes that risk sharper, not softer.

**AWS Builder ID and the credits form are clock-bound, not effort-bound.** Builder ID is a
required field. Credits close Sep 11 12pm PT. Both are minutes of work that become impossible if
missed.

**The live demo link is the cheapest Technical Implementation point available** — `publish.sh`
already exists; it needs one real, non-offline run. AgentCore is the expensive one, and the rules
are explicit that it is *not required*.

**The holdout result goes in the README whatever it says.** Criterion 3 asks whether the solution
addresses the problem "based on what's demonstrated" — a recorded honest evaluation is evidence;
a claim is not. The near-miss decline is the same argument in video form, and offline mode
structurally cannot show it.

Ordering that follows: unblock Bedrock → real runs → prompt tuning → **video** → live demo link →
Builder ID + Devpost text → builder.aws posts → submit. Deployment and Discord intake stay cut
unless everything above is done.

---

## 6 · Eligibility and housekeeping

- Open worldwide to individuals at the age of majority, teams, and organisations — **except**
  residents of a list including Argentina, Australia, Brazil, Hong Kong, Indonesia, Italy,
  Malaysia, Philippines, Thailand, Vietnam, Singapore, Quebec, Russia, Belarus, UAE, and
  OFAC-sanctioned territories. Check your own jurisdiction against
  [[REQUIREMENTS]] §3 before investing further.
- Register on Devpost ("Join Hackathon") — registration is what enables submission and the
  credits request.
- Prizes: $40,000 total. Grand Prize $10,000 (all tracks) + Gold $5,000 / Silver $3,000 /
  Bronze $2,000 per track. Winners are verified before payment; tax forms (W-9/W-8BEN) may be
  required.
- Entrants keep IP in their submissions; AWS/Devpost get a licence to judge and publicise.
- AWS credits expire **Oct 31, 2026** and any overspend is the entrant's own cost — the
  zero-spend budget alert in [[CHECKLIST]] §1 is the mitigation.

---

## 7 · Discrepancies noticed in the source

- Two different AWS credit request forms are given: `forms.gle/Ssr8zLw4afKg114M7` (Setup section)
  and `forms.gle/6sjzKiX6bKUMA5NEA` (Official Rules §4). The rules text governs where documents
  conflict (§11.4), so **use the second**, or reach the form via the Devpost Resources tab.
- The hashtag change described in §4 above.
