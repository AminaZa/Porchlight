---
tags: [product, impeccable, porchlight]
status: approved
created: 2026-09-02
---

# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Existing codebase. Python 3.12 renders every web surface as **one self-contained
HTML file** — inline CSS, inline SVG, no CDN, no build step, no external assets.
`src/render.py` generates `out/report.html`; the file is opened by double-click
or uploaded to S3 as a static site.

**Confirmed 2026-09-02:** a small *inline* script is permitted (scroll reveals,
replay controls, an interactive timeline). The self-contained rule still holds —
no CDN, no network request, one file. Everything must degrade to a readable page
with JavaScript disabled, because the file is also screen-recorded.

## Users

**Primary — residents of a neighbourhood zone.** People who joined a
neighbourhood channel, were buzzed for everything, and muted it. They are not
watching for alerts; they need the rare message to be worth opening. They are
non-technical and read on a phone.

**The volunteer approver.** Not the beneficiary — the *control*. Every alert is
drafted by the agent and sent by a person (`FNA_REQUIRE_APPROVAL`). Resolved
2026-08-21: alerts broadcast to `zone_residents`, so the volunteer is no longer
the customer. Do not reintroduce copy that frames this as a tool for whoever
runs the channel.

**Evaluators (this surface's readers).** Hackathon judges opening the published
link, most of whom must resell the idea to non-technical people. Recorded
because it is a factual part of how the product is currently evaluated, not as
a permanent audience.

## Product Purpose

Read every report a neighbourhood files so no human has to, and tell a street
the one thing worth knowing — which most weeks is nothing at all. Success is a
small number of alerts that are read, not a large number that are muted. On the
demonstration run: 38 reports in, 37 never surface to anyone, 1 alert out.

## Positioning

**The product is what it declines to send.** Three mechanisms a neighbouring
product could not truthfully copy:

1. **Correlation by meaning, not words.** The genuine cluster is four neighbours
   describing one place four ways — *mailboxes*, *post boxes*, *where the
   packages get dropped*, *delivery lockers* — sharing no content word. Keyword
   matching cannot see it and a similarity threshold cannot separate it from
   coincidence.
2. **The evidence is counted by the pipeline, not reported by the model.** How
   many reports, how many *distinct* reporters, over what span. A safety control
   a model self-reports is not a control.
3. **Redaction is enforced in code, not requested in a prompt.** `src/guards.py`
   hooks `AfterModelCallEvent`, retries on a leak, and fails closed.

## Operating Context

Reports arrive as ordinary sentences via a CLI (`src.intake.cli`) or the demo
runner over a 38-report seed set. Three Strands agents run in sequence on Amazon
Bedrock. Output surfaces are the terminal, a broadcast alert to a zone, and one
generated HTML page. That page is simultaneously the Devpost "Try it out" link,
the video's §3d and §5 footage, and the project's only visual artefact — one
file serving three deliverables.

Judging deadline **14 September 2026, 5:00pm PT** (Devpost).

## Capabilities and Constraints

- Three agents: **Haiku 4.5** triage · **Sonnet 4.6** correlation · **Opus 4.6**
  escalation, on Bedrock. This AWS account is not entitled to the 5-series.
- ChromaDB (vectors) + SQLite (rows) + numpy/scipy (per-zone anomaly z-score).
- `Audience = Literal["zone_residents"]` — the agent cannot choose a recipient.
- **`raw_text` is opt-in at all three boundaries** (`rendered_rows(include_raw=)`,
  `render.write(show_raw=)`, `--show-raw`). A renderer that gets reporters' own
  words by default is how the retention guarantee becomes a silent leak.
- **The page must stay generated from run data.** Every node position derives
  from a content hash; nothing is hand-placed. Both the page and the terminal
  bucket through `models.outcome_of` so they cannot print different tallies.
- Offline mode stubs the escalation judgment and must carry a visible band.
- The silent/declined split moves by one between runs. Only `38 in, 1 alert out`
  is fixed. Never hard-code the split.

## Brand Commitments

`BRANDING.md` is binding and approved. Summarised, not superseded:

- **Palette — amber on dusk.** Dusk `#0B1120` · Porch `#141E33` · Sill `#243352`
  · Lamp `#FFB454` · Halo `#FFE2AE` · Ember `#E08A34` · Chalk `#E9EEF7` ·
  Dim `#8FA0BC`.
- **The one rule that matters: Lamp never appears on anything that is not an
  escalation.** Not buttons, not links, not headers, not decorative underlines.
  The moment amber becomes decoration the restraint argument collapses.
  Dim = silently logged. Lit = the porch light came on.
- **Type:** Georgia for wordmark and headings (bookish, civic — deliberately not
  Inter). System sans for body. Monospace for anything the agent *measured*.
  **No webfonts anywhere** — zero network requests, no FOUT on camera.
- Name **Porchlight**; tagline *your friendly neighborhood agent*.
- **Never:** "spidey", costume red, character silhouettes, Marvel-derived faces.
- Alert and silent-log cards are *one component with a variant*, not two.

## Evidence on Hand

Real and quotable:

- **Run 4, 2026-09-01** — 38 reports, 1 alert. Alerts on the **3rd** report:
  3 reports · 3 distinct reporters · 13 hours · z = 6.5; the 4th is suppressed;
  final cluster z = 9.0. One genuine decline: 4 reports, 1 reporter.
- **Holdout, 2026-08-31 — 20 of 20.** Written before tuning, run once, never to
  be re-run. `data/holdout_result_2026-08-31.log`. **It proves the agent finds a
  hard cluster and resists a lexical trap; it produced zero declines, so it does
  not prove it can refuse a plausible one.** Publish the caveat with the number.
- **Cost:** ~$9.39 across ~190 reports processed — roughly **5 cents a report**,
  ~$1.80 per 38-report run. From the AWS credits page, 2026-09-02.
- 55 tests passing, 13 skipped. Three published builder.aws.com posts.

Must not be fabricated: there are **no real users, no deployment, and no real
incidents**. Every report is invented fixture data and the page says so.
Similarity figures exist in `README.md` but the user has **excluded them from
this page** — do not print them here.

## Product Principles

1. **Silence is the feature.** Any design that makes the page feel busy or
   alarming argues against the product.
2. **Show, don't assert.** Four phrasings collapsing into one stored sentence
   beats any paragraph claiming semantic matching works.
3. **The page cannot be able to lie.** It is generated from the run; if the data
   changes the page follows. Nothing hand-placed, nothing hard-coded.
4. **Name what it does not prove.** Every published number carries its limit.
5. **A place to watch, never a person to look for.**

## Accessibility & Inclusion

- AA minimum: Chalk 16:1, Dim 6.9:1 on Dusk. Any new pairing must be checked.
- **Never encode meaning in amber alone** — every lit state also carries a text
  label. A colour-blind reader and a compressed 1080p video frame must both
  resolve it.
- Readable on a phone; the primary user reads on one.
- Must survive YouTube compression — no hairline strokes, no sub-12px type in
  anything intended for camera.
- Respect `prefers-reduced-motion`; the page is screen-recorded and motion must
  never be required to understand it.
