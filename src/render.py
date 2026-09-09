"""Render a finished run as one self-contained HTML file.

Inline style, inline SVG, one short inline script, no CDN, no build step — open
it with a double-click, or upload it to S3 as a static site.

Three rules this module exists to enforce:

**The layout is deterministic.** Every position is derived from the report id,
which is itself a hash of the report's content. The same seed set always draws
the same picture, so a take can be re-shot in week six without the graph
shifting under the voiceover.

**Nothing is hand-placed.** If the seed data changes the picture follows it
automatically, because a diagram that has been arranged by hand is an
illustration, not evidence.

**Nothing is asserted that the rows do not contain.** Every figure on the page
is counted from the run. The handful of facts that are *about* the project
rather than about the rows — the holdout, the measured cost — are declared
once below with their source, and carry what they do not prove.

Composition is the surface direction locked on 2026-09-02, "What you heard /
what happened": the page splits the way the product does. One side is the
single message that reached a neighbour; the other is everything that was kept
from them. Palette, type and the amber-means-escalation-only rule come from
BRANDING.md and are not this file's to change.
"""

from __future__ import annotations

import hashlib
import html
from datetime import datetime
import math
import os
import re
from pathlib import Path

from src.tools import storage

# BRANDING.md § Palette
DUSK = "#0B1120"
PORCH = "#141E33"
SILL = "#243352"
NEAR = "#5C7098"
LAMP = "#FFB454"
HALO = "#FFE2AE"
EMBER = "#E08A34"
CHALK = "#E9EEF7"
DIM = "#8FA0BC"

# Set by demo/run_demo.py --offline. When true the page carries a band saying
# the judgment was stubbed, so a screenshot of it can never be mistaken for the
# agent working. See demo/offline.py.
OFFLINE = False

# Facts about the project rather than about this row set. Declared here, with
# their source, so they can be checked — and never restated anywhere else in
# this file. A number that appears twice is a number that can disagree with
# itself.
HOLDOUT = {
    "passed": 20,
    "total": 20,
    "date": "31 August 2026",
    "source": "data/holdout_result_2026-08-31.log",
    # Published with the number, never after it. The run produced zero
    # declines, so it shows the agent finding a hard cluster and resisting a
    # lexical trap; it does not show it refusing a plausible one.
    "limit": "It produced zero declines, so it does not show the agent "
             "refusing a cluster that looked real.",
}
COST = {
    "per_report_cents": 5,
    "source": "$9.39 of Bedrock spend across roughly 190 reports processed, "
              "read from the AWS credits page on 2 September 2026",
}

# The map's frame. Squarer than a banner because it sits beside the refusal
# rather than spanning the page, and a diagram that shrinks into a miniature
# has stopped being a diagram.
W, H = 640.0, 460.0
MARGIN = 34.0
MIN_SEP = 30.0          # keeps the field from collapsing into an unreadable clump
CLUSTER_RADIUS = 46.0

_ONES = ("zero one two three four five six seven eight nine ten eleven twelve "
         "thirteen fourteen fifteen sixteen seventeen eighteen nineteen").split()
_TENS = {2: "twenty", 3: "thirty", 4: "forty", 5: "fifty",
         6: "sixty", 7: "seventy", 8: "eighty", 9: "ninety"}


def _words(n: int) -> str:
    """Small numbers spelled out, for the one line that is prose rather than
    measurement. Anything this cannot spell stays a numeral rather than being
    approximated."""
    if 0 <= n < 20:
        return _ONES[n]
    if 20 <= n < 100:
        tens, ones = divmod(n, 10)
        return _TENS[tens] + (f"-{_ONES[ones]}" if ones else "")
    return str(n)


def _rand(seed: str, salt: str) -> float:
    """A stable float in [0,1) from a report id. Deterministic across runs,
    across machines, and across Python's hash randomisation."""
    digest = hashlib.sha256(f"{seed}:{salt}".encode()).digest()
    return int.from_bytes(digest[:8], "big") / float(1 << 64)


def _components(rows: list[dict]) -> list[list[str]]:
    """Group reports into clusters via their related-id links (union-find)."""
    parent: dict[str, str] = {r["report_id"]: r["report_id"] for r in rows}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: str, b: str) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[max(ra, rb)] = min(ra, rb)

    known = set(parent)
    for r in rows:
        for other in r["related_ids"]:
            if other in known:
                union(r["report_id"], other)

    groups: dict[str, list[str]] = {}
    for rid in parent:
        groups.setdefault(find(rid), []).append(rid)
    return [sorted(g) for g in groups.values()]


def _layout(rows: list[dict]) -> dict[str, tuple[float, float]]:
    """Place every node. Clusters cohere; singletons spread evenly.

    Groups are seated first, each claiming a region. Singletons are then dealt
    into a jittered grid rather than sampled at random — pure rejection
    sampling leaves the field visibly clumped in one corner with dead space
    elsewhere, and a picture that looks arbitrary reads as decorative.
    """
    pos: dict[str, tuple[float, float]] = {}
    groups = sorted(_components(rows), key=lambda g: (-len(g), g[0]))
    clusters = [g for g in groups if len(g) > 1]
    singles = [g[0] for g in groups if len(g) == 1]

    # Seat clusters along a jittered horizontal band, well apart from each other.
    centroids: list[tuple[float, float]] = []
    for i, group in enumerate(clusters):
        slots = max(len(clusters), 1)
        span = (W - 2 * (MARGIN + CLUSTER_RADIUS)) / slots
        cx = MARGIN + CLUSTER_RADIUS + span * (i + 0.5)
        cy = H * (0.34 + 0.32 * _rand(group[0], "cy"))
        centroids.append((cx, cy))

        # Members go at evenly spaced angles, not random ones. Random angles
        # let two members land 3px apart, and a four-report cluster then
        # renders as two blobs with edges going nowhere — which is what the
        # first version of this did. The whole seeded rotation still varies
        # per cluster, so the arrangement is deterministic without being rigid.
        n = len(group)
        rotation = _rand(group[0], "rot") * math.tau
        step = math.tau / n
        # Keep adjacent members at least MIN_SEP apart: chord = 2r·sin(π/n).
        radius = max(CLUSTER_RADIUS, MIN_SEP / (2 * math.sin(math.pi / n))) if n > 1 else 0.0

        for j, rid in enumerate(group):
            # Jitter is bounded to well under the angular step so it can
            # never close the gap to a neighbour.
            angle = rotation + j * step + (_rand(rid, "aj") - 0.5) * step * 0.30
            dist = radius * (0.88 + 0.24 * _rand(rid, "dj"))
            pos[rid] = (
                min(max(cx + math.cos(angle) * dist, MARGIN), W - MARGIN),
                min(max(cy + math.sin(angle) * dist, MARGIN), H - MARGIN),
            )

    if not singles:
        return pos

    # Deal singletons into grid cells, seeded so the assignment is stable.
    cols = max(1, round(math.sqrt(len(singles) * W / H)))
    rows_n = max(1, math.ceil(len(singles) / cols))
    cell_w = (W - 2 * MARGIN) / cols
    cell_h = (H - 2 * MARGIN) / rows_n

    order = sorted(singles, key=lambda r: _rand(r, "cell"))
    for idx, rid in enumerate(order):
        col, row = idx % cols, idx // cols
        x = MARGIN + cell_w * (col + 0.2 + 0.6 * _rand(rid, "jx"))
        y = MARGIN + cell_h * (row + 0.2 + 0.6 * _rand(rid, "jy"))

        # Nudge out of any cluster's personal space so groups stay legible.
        for cx, cy in centroids:
            dx, dy = x - cx, y - cy
            dist = math.hypot(dx, dy) or 1.0
            keep_out = CLUSTER_RADIUS + MIN_SEP
            if dist < keep_out:
                x = min(max(cx + dx / dist * keep_out, MARGIN), W - MARGIN)
                y = min(max(cy + dy / dist * keep_out, MARGIN), H - MARGIN)
        pos[rid] = (x, y)
    return pos


def _node_style(row: dict, alerted: set[str]) -> tuple[str, float]:
    """Colour and radius. Amber marks escalation and nothing else."""
    if row["report_id"] in alerted:
        return HALO, 7.5
    if row["cluster_size"] > 1:
        return NEAR, 6.5      # correlated, deliberately not escalated
    return SILL, 4.5          # silently logged, most of the picture


def _alerted(rows: list[dict]) -> set[str]:
    """Every report the run's alerts cover.

    Not only the ones linked from the report that happened to trigger an
    alert: a later report joining the cluster is suppressed rather than
    re-alerted (storage.alert_coverage), and treating it as unlit would show a
    four-report situation as a three-report one.
    """
    by_id = {r["report_id"] for r in rows}
    lit = {r["report_id"] for r in rows if r["covered"]}
    for r in rows:
        if r["action"] == "alert":
            lit.add(r["report_id"])
            lit.update(x for x in r["related_ids"] if x in by_id)
    return lit


def _svg(rows: list[dict]) -> str:
    """The whole run as one picture.

    Node circles are written with single-quoted attributes in a fixed order.
    tests/test_pipeline.py parses exactly that shape to assert every report got
    a node and that no two nodes overlap, so every *decorative* svg elsewhere
    on this page uses double quotes and cannot be mistaken for a report.
    """
    pos = _layout(rows)
    alerted = _alerted(rows)

    parts: list[str] = [
        f'<svg viewBox="0 0 {W:.0f} {H:.0f}" role="img" '
        f'aria-label="Every report in the run. Dim nodes were logged silently; '
        f'mid-tone nodes were correlated but declined; amber nodes form the one '
        f'escalated cluster.">',
        "<defs><radialGradient id='glow' cx='50%' cy='50%' r='50%'>"
        f"<stop offset='0%' stop-color='{LAMP}' stop-opacity='0.30'/>"
        f"<stop offset='100%' stop-color='{LAMP}' stop-opacity='0'/>"
        "</radialGradient></defs>",
    ]

    # Glow behind each alerted cluster, drawn first so it sits underneath.
    if alerted:
        xs = [pos[i][0] for i in alerted]
        ys = [pos[i][1] for i in alerted]
        cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)
        radius = max(max((abs(x - cx) for x in xs), default=0),
                     max((abs(y - cy) for y in ys), default=0)) + 58
        parts.append(f"<circle cx='{cx:.1f}' cy='{cy:.1f}' r='{radius:.1f}' fill='url(#glow)'/>")

    # Edges only inside the escalated cluster. Declined clusters stay visibly
    # unlinked — that absence is the most persuasive thing on the page.
    ordered = sorted(alerted)
    parts.append(f"<g stroke='{LAMP}' stroke-width='1.5' opacity='0.75'>")
    for i, a in enumerate(ordered):
        for b in ordered[i + 1:]:
            (x1, y1), (x2, y2) = pos[a], pos[b]
            parts.append(f"<line x1='{x1:.1f}' y1='{y1:.1f}' x2='{x2:.1f}' y2='{y2:.1f}'/>")
    parts.append("</g>")

    for r in rows:
        x, y = pos[r["report_id"]]
        colour, radius = _node_style(r, alerted)
        title = html.escape(f"{r['zone']}: {r['summary'][:90]}")
        parts.append(
            f"<circle cx='{x:.1f}' cy='{y:.1f}' r='{radius}' fill='{colour}'>"
            f"<title>{title}</title></circle>"
        )

    parts.append("</svg>")
    return "".join(parts)


# --- authored marks ---------------------------------------------------------
#
# Drawn, at one stroke weight, rather than borrowed from a glyph table. Double
# quotes throughout: see _svg on why that separates them from report nodes.

def _mark_lamp(colour: str) -> str:
    """The porch light, on. Used only where something escalated."""
    return (
        f'<svg class="ico" viewBox="0 0 16 16" aria-hidden="true" fill="none" '
        f'stroke="{colour}" stroke-width="1.4" stroke-linecap="round">'
        f'<path d="M8 2.4v1.9M3.6 4.2l1.3 1.3M12.4 4.2l-1.3 1.3"/>'
        f'<circle cx="8" cy="9.2" r="3.1" fill="{colour}" stroke="none"/>'
        f'<path d="M5.2 13.6h5.6"/></svg>'
    )


def _mark_rule(colour: str) -> str:
    """A line under a line. Used where something was written down and left."""
    return (
        f'<svg class="ico" viewBox="0 0 16 16" aria-hidden="true" fill="none" '
        f'stroke="{colour}" stroke-width="1.4" stroke-linecap="round">'
        f'<path d="M2.6 6.2h10.8M2.6 9.8h6.6"/></svg>'
    )


def _card(row: dict, kind: str, lead: bool = False) -> str:
    """One component, two variants — BRANDING.md § Applied.

    Only the accent and the kicker change between an escalation and a refusal,
    because building them as two components is how a page stops showing that
    restraint is the same machinery as alarm.
    """
    alert = kind == "alert"
    accent = LAMP if alert else SILL
    label_colour = LAMP if alert else DIM
    icon = _mark_lamp(LAMP) if alert else _mark_rule(DIM)
    kicker = "Sent to this zone" if alert else "Correlated, not sent"
    body = row["message"] if alert else row["reasoning"]
    n = row["distinct_reporters"]
    foot = (
        f"{row['cluster_size']} reports · {n} reporter{'' if n == 1 else 's'} · "
        f"{row['time_span_hours']:.0f}h · z={row['anomaly_score']:.1f}"
    )
    return (
        f"<div class='card{' card--lead' if lead else ''}' "
        f"style='border-left-color:{accent}'>"
        f"<p class='kicker' style='color:{label_colour}'>{icon}"
        f"<span>{html.escape(kicker)}, {html.escape(row['zone'])}</span></p>"
        f"<p class='body'>{html.escape(body)}</p>"
        f"<p class='foot'>{html.escape(foot)}</p></div>"
    )


def _span(rows: list[dict]) -> str:
    """How much ground the run actually covers, counted rather than claimed.

    An earlier draft of this page called it "one street, last night". The rows
    say several zones over several days, and a page whose own header overstates
    its scope has no business asking to be believed further down.
    """
    zones = len({r["zone"] for r in rows})
    stamps = sorted(r["timestamp"] for r in rows)
    days = ""
    try:
        first = datetime.fromisoformat(stamps[0])
        last = datetime.fromisoformat(stamps[-1])
        n = max(1, round((last - first).total_seconds() / 86400))
        days = f" · {n} day{'' if n == 1 else 's'}"
    except (IndexError, TypeError, ValueError):
        pass
    return f"{len(rows)} reports · {zones} zone{'' if zones == 1 else 's'}{days}"


def _when(ts: str) -> str:
    """A timestamp a reader can hold in their head, not an ISO string."""
    try:
        return datetime.fromisoformat(ts).strftime("%d %b · %H:%M")
    except (TypeError, ValueError):
        return ts or ""


def _fold(rows: list[dict], tally: str) -> str:
    """The first viewport: what one neighbour got, beside what they did not.

    Left is the single message, at reading size, as it was broadcast. Right is
    every report in the run drawn as one small mark each — the silence, given a
    shape. The marks are ordered by arrival, so the column reads as the night
    passing rather than as a chart.
    """
    total = len(rows)
    alerts = [r for r in rows if r["outcome"] == "alert"]
    lit = _alerted(rows)
    # Exactly the reports that render as a plain mark: everything the run's
    # alerts do not cover. Never total - len(alerts), which double-counts the
    # cluster members that are drawn ringed rather than plain.
    quiet = total - len(lit)

    marks = []
    for r in sorted(rows, key=lambda r: r["timestamp"]):
        if r["outcome"] == "alert":
            cls = "mark lit"          # the one that sent
        elif r["report_id"] in lit:
            cls = "mark cov"          # same situation, no second message
        else:
            cls = "mark"
        # The title is the only place a quiet report says anything at all.
        tip = html.escape(f"{r['zone']} · {_when(r['timestamp'])} · {r['outcome']}")
        marks.append(f"<span class='{cls}' title='{tip}'></span>")

    # Said only when the run actually has a covered cluster to explain.
    key = ""
    if alerts and len(lit) > 1:
        key = (
            f"The {_words(len(lit) - 1)} ringed marks belong to the same "
            f"situation as the lit one, and produced no second message. The "
            f"other "
        )
    else:
        key = "The other " if alerts else "All "

    if alerts:
        headline = (
            f"{_words(total).capitalize()} reports came in. "
            f"<span class='lit'>You heard one.</span>"
        )
        left = _card(alerts[0], "alert", lead=True)
        stand = (
            "That is the whole of what Porchlight sent. One message, to "
            "the people who live on that street, drafted by the agent and "
            "released by a person."
        )
    else:
        # A run can legitimately end with nothing to send. Say so plainly
        # rather than rendering an empty slot that reads as a broken page.
        headline = (
            f"{_words(total).capitalize()} reports came in. "
            f"<span class='lit'>You heard nothing.</span>"
        )
        left = (
            "<div class='card'><p class='kicker' style='color:" + DIM + "'>"
            + _mark_rule(DIM) + "<span>Nothing was sent</span></p>"
            "<p class='body'>No situation in this run met the bar to interrupt "
            "anyone. Every report was logged and left.</p></div>"
        )
        stand = ("Most runs end here. A service that says nothing on a quiet "
                 "night is the product working, not failing.")

    return f"""
  <section class="fold">
    <div class="heard">
      <h1>{headline}</h1>
      {left}
      <p class="stand">{stand}</p>
    </div>
    <div class="unheard">
      <h2>And this is everything else that came in.</h2>
      <div class="marks">{''.join(marks)}</div>
      {tally}
      <p class="stand">{key}{_words(quiet)} were read, weighed and left where
      they were. Nobody was notified, nobody was woken, and nobody was
      described. Hover any mark to see what it was.</p>
    </div>
  </section>"""


def _transcript(rows: list[dict]) -> str:
    """The reports as neighbours wrote them, beside what Porchlight kept.

    This is the page's argument, made without a paragraph of explanation. On
    the left, several people describe one situation and share almost no words.
    On the right, the normalized sentences that actually get indexed. A reader
    sees in one glance both why keyword matching cannot work here and what the
    redaction guarantee removes, which are the two claims this project rests on.

    Short by design: the alerted cluster plus two quiet reports for contrast.
    The full run is the map; this is the part that goes on camera.

    The right column is *not* annotated with which words were removed. That
    diff is not in the data — a word absent from the summary is usually just a
    rephrasing — and inventing the highlight would be asserting something the
    run did not record.
    """
    if not any("raw_text" in r for r in rows):
        return ""

    cluster = [r for r in rows if r["covered"] or r["outcome"] == "alert"]
    if not cluster:
        return ""
    in_cluster = {r["report_id"] for r in cluster}

    # Two silent reports from around the same time, so the contrast is between
    # things the agent saw together rather than against some unrelated one-off.
    #
    # The cluster's own early reports are silent too -- they arrived before
    # there was anything to correlate them with -- so they qualify on outcome
    # and have to be excluded by id, or a report is drawn twice.
    first = datetime.fromisoformat(cluster[0]["timestamp"])
    quiet = sorted(
        (r for r in rows
         if r["outcome"] == "silent" and r["report_id"] not in in_cluster),
        key=lambda r: abs(
            (datetime.fromisoformat(r["timestamp"]) - first).total_seconds()
        ),
    )[:2]

    turns = []
    for i, row in enumerate(sorted(cluster + quiet, key=lambda r: r["timestamp"])):
        lit = row["report_id"] in in_cluster
        raw = row.get("raw_text")
        # None once the retention timer has run. Say so rather than drawing an
        # empty bubble, because an empty bubble reads as a rendering bug.
        said = (
            html.escape(raw) if raw
            else "<i>deleted, past the retention window</i>"
        )
        tag = (
            "<span class='tag lit'>escalated cluster</span>" if lit
            else "<span class='tag'>logged silently</span>"
        )
        # The class string 'turn lit' is asserted verbatim by
        # tests/test_pipeline.py to check the highlight matches the cluster.
        turns.append(
            f"<div class='turn{' lit' if lit else ''}' style='--i:{i}'>"
            f"<div class='said'><p class='msg'>{said}</p>"
            f"<p class='meta'>{html.escape(row['zone'])} · {_when(row['timestamp'])}"
            f" · {html.escape(row['report_id'][:6])}</p></div>"
            f"<div class='kept'><p class='norm'>{html.escape(row['summary'])}</p>"
            f"<p class='meta'>{tag}</p></div></div>"
        )

    head = (
        "<div class='thead'><span>What neighbours typed</span>"
        "<span>What Porchlight kept</span></div>"
    )
    lede = (
        "These arrived as separate messages, hours and days apart, from people "
        "who had not spoken to each other. Read down the left column and they "
        "share almost no words. Read down the right and the agent has worked "
        "out which of them are the same situation."
    )

    # The convergence is only claimed when the rows actually show it: every
    # report the alert covers has to name one place. If a future run splits
    # across zones this line disappears rather than overstating.
    zones = {r["zone"] for r in cluster}
    converge = ""
    if len(zones) == 1 and len(cluster) > 1:
        place = html.escape(next(iter(zones)))
        shared = _shared_content_words([r.get("raw_text") or "" for r in cluster])
        phrase = (
            "not one content word in common"
            if not shared else
            f"only {_words(len(shared))} content word"
            f"{'' if len(shared) == 1 else 's'} in common"
        )
        converge = (
            f"<p class='converge'><span class='n'>{len(cluster)}</span> ways of "
            f"saying it, {phrase}, and one place: "
            f"<span class='place'>{place}</span></p>"
        )

    note = (
        "Only the right column is indexed or correlated. The left column is held "
        "briefly and deleted on a retention timer. Every report here is "
        "invented fixture data, and the raw text is off by default."
    )
    # The markup '<section class=\'transcript\'>' is asserted verbatim by
    # tests/test_pipeline.py as the thing that must be absent without --show-raw.
    return (
        "\n  <section class='transcript'>"
        "<h2>What was said, and what was stored</h2>"
        f"<p class='lede'>{lede}</p>"
        "<button class='replay' type='button' hidden>Replay</button>"
        f"{head}{''.join(turns)}{converge}"
        f"<p class='note'>{note}</p></section>\n"
    )


# Words too common to count as evidence of shared vocabulary. Deliberately
# short: the claim is about content words, and a long list would let the page
# manufacture the result it wants.
_STOP = set(
    "a an and the is was were be been being am are at by for from in into of on "
    "onto to with without over under near by again this that these those there "
    "here it its it's i we they he she him her them my our their your you me "
    "has have had do does did just some any not no nor so as but or if then "
    "when while about around out up down off back one two three four last night "
    "morning evening today tonight yesterday time times thing things".split()
)


def _shared_content_words(texts: list[str]) -> set[str]:
    """Content words present in every one of the given texts.

    Used only to state the premise in the transcript's own numbers rather than
    asserting it. If a future dataset does share vocabulary, the page says so.
    """
    sets = []
    for t in texts:
        words = {w for w in re.findall(r"[a-z']+", (t or "").lower())
                 if len(w) > 2 and w not in _STOP}
        if words:
            sets.append(words)
    if len(sets) < 2:
        return set()
    return set.intersection(*sets)


def _model_row(role: str, label: str, job: str) -> str:
    """One stage, named by the id that actually ran.

    Read through the same accessor the agents use, so the page cannot claim a
    model the run did not use. Falls back to the environment if the provider
    module will not import — the page has to render on a clean clone with no
    credentials.
    """
    try:
        from src.provider import model_id
        ident = model_id(role)  # type: ignore[arg-type]
    except Exception:
        ident = os.environ.get(f"FNA_MODEL_{role.upper()}", "").strip() or "not recorded"
    m = re.search(r"claude-(haiku|sonnet|opus)-(\d)-(\d)", ident)
    name = f"{m.group(1).capitalize()} {m.group(2)}.{m.group(3)}" if m else label
    return (
        f"<div class='spec'><p class='spec-k'>{html.escape(role.capitalize())}</p>"
        f"<p class='spec-v'>{html.escape(name)}</p>"
        f"<p class='spec-n'>{html.escape(job)}</p>"
        f"<p class='spec-id'>{html.escape(ident)}</p></div>"
    )


def _ledger(rows: list[dict], total: int) -> str:
    """Provenance, and the limits, in the same band.

    A page that publishes a result and hides what the result does not cover is
    doing the thing this project is arguing against, so the two sit together.
    """
    cost = COST["per_report_cents"]
    run_cost = cost * total / 100.0
    holdout = f"{HOLDOUT['passed']} of {HOLDOUT['total']}"
    return f"""
  <section class="ledger">
    <h2>Where these numbers come from</h2>
    <div class="specs">
      {_model_row("triage", "Haiku", "reads one report, strips the person, writes one sentence")}
      {_model_row("correlation", "Sonnet", "chooses its own lookups, decides what is related")}
      {_model_row("escalation", "Opus", "weighs the counted evidence and makes the call")}
    </div>
    <div class="facts">
      <p class="fact"><b>A held-out set of {HOLDOUT['total']} cases, written
      before any tuning began, passed {holdout}.</b> It was run once, on
      {html.escape(HOLDOUT['date'])}, and has not been run since: re-running a
      holdout after a prompt change turns it back into tuning data.
      {html.escape(HOLDOUT['limit'])}</p>
      <p class="fact"><b>Reading every report costs about {cost} cents
      each.</b> Around ${run_cost:.2f} to work through a month like this one,
      across all three models. Measured rather than estimated:
      {html.escape(COST['source'])}.</p>
    </div>
    <p class="limits"><b>What this page does not show.</b> Every report here is
    invented fixture data. There are no real users, no real incidents and no
    deployment behind it. The split between reports logged silently and reports
    correlated then declined moves by one between runs, so it is reported, not
    promised; only the totals are stable. And the agent is not always the thing
    that keeps a report quiet. Some are never linked to anything in the first
    place, which is retrieval separating them rather than judgment refusing them.</p>
  </section>"""


def _offline_band() -> str:
    """A band the reader cannot miss when the models were stubbed."""
    if not OFFLINE:
        return ""
    return (
        '<div class="offline">OFFLINE MODE — the escalation decision below came '
        "from a hard-coded rule, not from a model. Retrieval, the anomaly "
        "detector and the evidence counts are real; the judgment is not.</div>"
    )


def _suppressed_clause(n: int) -> str:
    """The terminal prints suppressed only when there are any. Match it."""
    return f" · {n} suppressed as duplicates" if n else ""


def build_html(rows: list[dict]) -> str:
    """The whole page as a string.

    Rows carrying a raw_text key get the transcript section; rows without it
    render exactly as before. That keeps the reporter's own words an explicit
    decision at the call site rather than a property of the template.
    """
    total = len(rows)
    alerts = [r for r in rows if r["outcome"] == "alert"]

    # Bucket by the stored outcome, never by re-deriving it here. Deriving it
    # a second way is what made this page and the terminal print two different
    # tallies for one run — see models.outcome_of.
    declined = [r for r in rows if r["outcome"] == "declined"]
    suppressed = [r for r in rows if r["outcome"] == "suppressed"]
    silent = sum(r["outcome"] == "silent" for r in rows)

    # The refusal card draws from anything correlated, suppressed duplicates
    # included, because the filter below excludes covered rows anyway.
    correlated = declined + suppressed

    # The strongest genuine refusal. "Genuine" excludes anything an alert
    # already covers: a report suppressed as a duplicate of the alert above it
    # is a footnote, and putting it here spends the page's second-most valuable
    # slot restating the alert instead of showing the thing the product is
    # actually about — a situation that looked alarming and was not escalated.
    genuine = [r for r in correlated if not r["covered"]]
    if genuine:
        best = max(genuine, key=lambda r: (r["cluster_size"], r["distinct_reporters"]))
        refusal = _card(best, "decline")
        refusal_stand = (
            f"{_words(best['cluster_size']).capitalize()} reports, one place, a "
            f"tight window, and "
            f"{_words(best['distinct_reporters'])} "
            f"{'person' if best['distinct_reporters'] == 1 else 'people'} behind "
            f"{'them' if best['distinct_reporters'] != 1 else 'all of them'}. "
            "The agent found the pattern, looked at who filed it, and did not "
            "send it. Nobody heard about this. Nobody got talked about."
        )
    else:
        refusal = ""
        refusal_stand = (
            "This run correlated nothing it then refused. That is a property of "
            "the night, not a claim about the agent."
        )

    tally = (
        f'<p class="tally">{total} reports · {silent} logged silently · '
        f'{len(declined)} correlated and declined'
        f'{_suppressed_clause(len(suppressed))} · '
        f'<b>{len(alerts)} alert{"" if len(alerts) == 1 else "s"}</b></p>'
    )

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Porchlight: {total} reports, {len(alerts)} message{'' if len(alerts) == 1 else 's'}</title>
<style>
  :root {{
    color-scheme: dark;
    --dusk:{DUSK}; --porch:{PORCH}; --sill:{SILL}; --near:{NEAR};
    --lamp:{LAMP}; --halo:{HALO}; --ember:{EMBER}; --chalk:{CHALK}; --dim:{DIM};
    --serif: Georgia,"Times New Roman",serif;
    --sans: -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
    --mono: ui-monospace,"Cascadia Code","SF Mono",Consolas,monospace;
    --ease: cubic-bezier(.16,1,.3,1);
  }}
  * {{ box-sizing: border-box; }}
  html {{ scrollbar-color: var(--sill) var(--dusk); }}
  body {{ margin:0; background:var(--dusk); color:var(--chalk);
    padding:0 1.5rem 5rem; font-family:var(--sans); line-height:1.6;
    -webkit-font-smoothing:antialiased; }}
  ::selection {{ background:rgba(255,180,84,.24); color:var(--chalk); }}
  ::-webkit-scrollbar {{ width:11px; height:11px; }}
  ::-webkit-scrollbar-track {{ background:var(--dusk); }}
  ::-webkit-scrollbar-thumb {{ background:var(--sill); border-radius:99px;
    border:3px solid var(--dusk); }}
  ::-webkit-scrollbar-thumb:hover {{ background:var(--near); }}
  :focus-visible {{ outline:2px solid var(--halo); outline-offset:3px;
    border-radius:2px; }}
  a {{ color:var(--chalk); text-underline-offset:.2em;
    text-decoration-color:var(--sill); }}
  .wrap {{ max-width:74rem; margin:0 auto; }}

  /* masthead */
  .top {{ display:flex; justify-content:space-between; align-items:baseline;
    gap:1.5rem; flex-wrap:wrap; padding:2.6rem 0 4.5rem;
    border-bottom:1px solid var(--sill); margin-bottom:3.5rem; }}
  .word {{ font-family:var(--serif); font-size:1.32rem; letter-spacing:-.02em;
    margin:0; font-weight:400; }}
  .word .lit {{ color:var(--lamp); }}
  .word i {{ display:block; font-size:.86rem; color:var(--dim);
    letter-spacing:0; margin-top:.1rem; }}
  .runmeta {{ font-family:var(--mono); font-size:.75rem; color:var(--dim);
    margin:0; text-align:right; font-variant-numeric:tabular-nums; }}

  /* the fold: what you heard | what you did not */
  .fold {{ display:grid; grid-template-columns:1.15fr .85fr; gap:4rem;
    align-items:start; }}
  .fold > *, .row2 > *, .turn > *, .thead > * {{ min-width:0; }}
  h1 {{ font-family:var(--serif); font-weight:400;
    font-size:clamp(2.1rem,4.4vw,3.4rem); letter-spacing:-.033em;
    line-height:1.07; margin:0 0 2rem; text-wrap:balance; max-width:18ch; }}
  h1 .lit {{ color:var(--lamp); }}
  .unheard h2 {{ font-family:var(--serif); font-weight:400; font-size:1.32rem;
    letter-spacing:-.02em; line-height:1.25; margin:.4rem 0 1.6rem;
    color:var(--chalk); max-width:22ch; }}
  .stand {{ color:var(--dim); font-size:.9rem; max-width:52ch;
    margin:1.5rem 0 0; }}

  /* the silence, given a shape */
  .marks {{ display:flex; flex-wrap:wrap; gap:8px; max-width:24rem;
    margin-bottom:1.4rem; }}
  .mark {{ width:17px; height:17px; border-radius:2px; background:var(--sill);
    display:block; }}
  .mark.cov {{ box-shadow:inset 0 0 0 2px var(--lamp); }}
  .mark.lit {{ background:var(--lamp);
    box-shadow:0 2px 12px rgba(255,180,84,.45); }}

  /* one component, two variants — BRANDING.md */
  .card {{ background:var(--porch); border-left:3px solid var(--sill);
    border-radius:2px; padding:1.3rem 1.5rem;
    box-shadow:0 14px 34px -22px rgba(0,0,0,.9); }}
  .card--lead {{ padding:1.7rem 1.9rem; }}
  .card .kicker {{ font-size:.75rem; text-transform:uppercase;
    letter-spacing:.12em; font-weight:700; margin:0 0 .75rem;
    display:flex; align-items:center; gap:.5rem; }}
  .ico {{ width:15px; height:15px; flex:none; }}
  .card .body {{ font-size:.95rem; margin:0 0 .9rem; max-width:62ch; }}
  .card--lead .body {{ font-size:1.06rem; }}
  .card .foot {{ font-family:var(--mono); font-size:.75rem; color:var(--dim);
    margin:0; font-variant-numeric:tabular-nums; }}

  /* said / kept */
  .transcript {{ margin-top:6rem; position:relative; }}
  .transcript h2, .ledger h2 {{ font-family:var(--serif); font-weight:400;
    font-size:1.75rem; letter-spacing:-.025em; margin:0 0 .7rem; }}
  .transcript .lede {{ color:var(--dim); max-width:66ch; margin:0 0 2rem;
    font-size:.94rem; }}
  .replay {{ position:absolute; top:.4rem; right:0; background:transparent;
    border:1px solid var(--sill); color:var(--dim); font:inherit;
    font-size:.75rem; letter-spacing:.06em; text-transform:uppercase;
    padding:.4rem .85rem; border-radius:2px; cursor:pointer;
    transition:border-color .2s, color .2s; }}
  .replay:hover {{ border-color:var(--near); color:var(--chalk); }}
  .thead, .turn {{ display:grid; grid-template-columns:1fr 1fr; gap:1.25rem; }}
  .thead {{ font-size:.75rem; text-transform:uppercase; letter-spacing:.13em;
    font-weight:700; color:var(--dim); padding-bottom:.7rem;
    border-bottom:1px solid var(--sill); margin-bottom:1.3rem; }}
  .turn {{ margin-bottom:1rem; align-items:start; }}
  .said {{ background:var(--porch); border-radius:14px 14px 14px 3px;
    padding:.9rem 1.15rem; }}
  .turn.lit .said {{ background:var(--sill); }}
  .said .msg {{ margin:0 0 .45rem; font-size:.93rem; }}
  .kept {{ border-left:2px solid var(--sill); padding:.2rem 0 .2rem 1.15rem; }}
  .turn.lit .kept {{ border-left-color:var(--lamp); }}
  .kept .norm {{ margin:0 0 .45rem; font-size:.95rem; color:var(--chalk);
    line-height:1.55; }}
  .turn.lit .kept .norm {{ color:var(--halo); }}
  .meta {{ font-family:var(--mono); font-size:.75rem; color:var(--dim);
    margin:0; font-variant-numeric:tabular-nums; }}
  .tag {{ text-transform:uppercase; letter-spacing:.1em; font-weight:700; }}
  .tag.lit {{ color:var(--lamp); }}
  .converge {{ font-family:var(--serif); font-size:1.2rem; color:var(--chalk);
    margin:2rem 0 0; padding-top:1.5rem; border-top:1px solid var(--sill);
    max-width:60ch; line-height:1.45; text-wrap:pretty; }}
  .converge .n {{ color:var(--dim); }}
  .converge .place {{ color:var(--lamp); font-family:var(--mono);
    font-size:.94rem; }}
  .transcript .note {{ color:var(--dim); font-size:.8rem; max-width:66ch;
    margin:1.6rem 0 0; }}

  /* the refusal, beside the field */
  .row2 {{ display:grid; grid-template-columns:5fr 7fr; gap:3.5rem;
    margin-top:6rem; align-items:start; }}
  .row2 h2 {{ font-family:var(--serif); font-weight:400; font-size:1.75rem;
    letter-spacing:-.025em; margin:0 0 1.3rem; max-width:16ch; }}
  .panel {{ background:var(--porch); border-radius:3px; padding:1.5rem;
    overflow-x:auto; }}
  .panel svg {{ display:block; width:100%; height:auto; min-width:19rem; }}
  .legend {{ display:flex; gap:1.4rem; flex-wrap:wrap; font-size:.8rem;
    color:var(--dim); margin:1.3rem 0 0; }}
  .legend span {{ display:inline-flex; align-items:center; gap:.5rem; }}
  .dot {{ width:10px; height:10px; border-radius:50%; display:inline-block;
    flex:none; }}
  .tally {{ font-family:var(--mono); font-size:.75rem; color:var(--dim);
    margin:0 0 1.5rem; font-variant-numeric:tabular-nums; line-height:1.9;
    max-width:26rem; }}
  .tally b {{ color:var(--lamp); font-weight:600; white-space:nowrap; }}

  /* provenance and limits */
  .ledger {{ margin-top:6rem; padding-top:3rem;
    border-top:1px solid var(--sill); }}
  .specs {{ display:grid; grid-template-columns:repeat(3,1fr); gap:1.5rem;
    margin:2rem 0 3rem; }}
  .spec-k {{ font-size:.75rem; text-transform:uppercase; letter-spacing:.13em;
    font-weight:700; color:var(--dim); margin:0 0 .35rem; }}
  .spec-v {{ font-family:var(--serif); font-size:1.3rem; margin:0 0 .3rem; }}
  .spec-n {{ font-size:.84rem; color:var(--dim); margin:0 0 .5rem;
    max-width:32ch; }}
  .spec-id {{ font-family:var(--mono); font-size:.75rem; color:var(--dim);
    margin:0; word-break:break-all; }}
  .facts {{ display:grid; grid-template-columns:1fr 1fr; gap:3rem;
    padding:2.2rem 0; border-top:1px solid var(--sill);
    border-bottom:1px solid var(--sill); }}
  .fact {{ font-size:.88rem; color:var(--dim); margin:0; max-width:52ch; }}
  .fact b {{ font-family:var(--serif); font-weight:400; font-size:1.25rem;
    line-height:1.3; color:var(--chalk); display:block; margin-bottom:.55rem;
    letter-spacing:-.015em; }}
  .claim {{ font-family:var(--serif); font-size:1.2rem; line-height:1.45;
    color:var(--chalk); margin:0 0 1.4rem; max-width:38ch;
    text-wrap:pretty; }}
  .limits {{ color:var(--dim); font-size:.86rem; max-width:70ch;
    margin:2rem 0 0; }}
  .limits b {{ color:var(--chalk); font-weight:600; }}

  footer {{ color:var(--dim); font-size:.8rem; margin-top:4rem;
    max-width:70ch; padding-top:1.6rem; border-top:1px solid var(--sill); }}
  .offline {{ background:var(--ember); color:var(--dusk); font-weight:700;
    text-align:center; padding:.75rem 1rem; margin:0 -1.5rem 2.5rem;
    font-size:.85rem; letter-spacing:.02em; }}

  /* The one authored moment: what was stored develops out of what was said,
     the way a print comes up in the tray. The sharp state is the default, so
     the page is complete with no script and under reduced motion; the blur is
     only ever added by the script below. */
  .dev .kept .norm, .dev .kept .meta {{ filter:blur(7px); opacity:.12;
    transition:filter 1s var(--ease), opacity 1s var(--ease);
    transition-delay:calc(var(--i,0) * 110ms); }}
  .dev .turn.seen .kept .norm, .dev .turn.seen .kept .meta {{
    filter:blur(0); opacity:1; }}
  @media (prefers-reduced-motion:reduce) {{
    .dev .kept .norm, .dev .kept .meta {{
      filter:none; opacity:1; transition:none; }}
  }}

  @media (max-width:1000px) {{
    .fold, .row2 {{ grid-template-columns:1fr; gap:3rem; }}
    .specs, .facts {{ grid-template-columns:1fr; gap:1.75rem; }}
    .marks {{ max-width:none; }}
  }}
  @media (max-width:640px) {{
    body {{ padding:0 1.15rem 3.5rem; }}
    .top {{ padding:1.4rem 0 1.9rem; margin-bottom:1.9rem; }}
    h1 {{ margin-bottom:1.5rem; }}
    .runmeta {{ text-align:left; }}
    .thead {{ display:none; }}
    .turn {{ grid-template-columns:1fr; gap:.5rem; }}
    .kept {{ margin-left:.9rem; }}
    .replay {{ position:static; margin:0 0 1.5rem; }}
    .transcript, .row2, .ledger {{ margin-top:4rem; }}
    .offline {{ margin:0 -1.15rem 2rem; }}
  }}
</style></head>
<body>{_offline_band()}<div class="wrap">
  <div class="top">
    <p class="word">Porch<span class="lit">light</span>
      <i>your friendly neighborhood agent</i></p>
    <p class="runmeta">{_span(rows)}<br>
      rendered {datetime.now().strftime('%d %b %Y · %H:%M')}</p>
  </div>
{_fold(rows, tally)}
{_transcript(rows)}
  <section class="row2">
    <div>
      <h2>And the one it refused.</h2>
      <p class="claim">{refusal_stand}</p>
      {refusal}
    </div>
    <div>
      <div class="panel">
        {_svg(rows)}
        <div class="legend">
          <span><i class="dot" style="width:9px;height:9px;background:{SILL}"></i>
            logged silently</span>
          <span><i class="dot" style="width:13px;height:13px;background:{NEAR}"></i>
            correlated, declined</span>
          <span><i class="dot" style="width:15px;height:15px;background:{HALO}"></i>
            escalated</span>
        </div>
      </div>
    </div>
  </section>
{_ledger(rows, total)}
  <footer>Generated from a run over the demonstration dataset in
  <code>data/seed_reports.json</code>. Every node is a real report processed by
  the pipeline; positions are derived from report content, not arranged by hand.
  Reports about people are stored only in redacted form.</footer>
</div>
<script>
/* Two behaviours, both optional. Without this script the page is complete and
   every word is already legible — the blur is added here, never authored into
   the default state. */
(function () {{
  var root = document.documentElement;
  root.classList.add('dev');
  var turns = [].slice.call(document.querySelectorAll('.turn'));
  var replay = document.querySelector('.replay');
  if (!turns.length) return;

  function show(el) {{ el.classList.add('seen'); }}

  if (!('IntersectionObserver' in window)) {{ turns.forEach(show); return; }}
  var io = new IntersectionObserver(function (entries) {{
    entries.forEach(function (e) {{ if (e.isIntersecting) {{ show(e.target); io.unobserve(e.target); }} }});
  }}, {{ threshold: 0.35, rootMargin: '0px 0px -8% 0px' }});
  turns.forEach(function (t) {{ io.observe(t); }});

  /* Re-shooting a take should not mean reloading the page. */
  if (replay) {{
    replay.hidden = false;
    replay.addEventListener('click', function () {{
      turns.forEach(function (t) {{ t.classList.remove('seen'); }});
      void document.body.offsetWidth;
      turns.forEach(show);
    }});
  }}
}})();
</script>
</body></html>
"""


def write(path: str | Path | None = None, show_raw: bool = False) -> Path:
    """Render the current database to a file. Returns the path written.

    show_raw pulls the reporters' own words into the transcript section. Off by
    default: see storage.rendered_rows on why that default is the guarantee.
    """
    out = Path(path or os.environ.get("FNA_HTML_OUT", "out/report.html"))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build_html(storage.rendered_rows(include_raw=show_raw)),
                   encoding="utf-8")
    return out


if __name__ == "__main__":
    import sys

    args = [a for a in sys.argv[1:] if a != "--show-raw"]
    print(write(args[0] if args else None, show_raw="--show-raw" in sys.argv))
