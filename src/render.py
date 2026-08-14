"""Render a finished run as one self-contained HTML file.

Inline style, inline SVG, no scripts, no CDN, no build step — open it with a
double-click, or upload it to S3 as a static site.

Two rules this module exists to enforce:

**The layout is deterministic.** Every position is derived from the report id,
which is itself a hash of the report's content. The same seed set always draws
the same picture, so a take can be re-shot in week six without the graph
shifting under the voiceover.

**Nothing is hand-placed.** If the seed data changes the picture follows it
automatically, because a diagram that has been arranged by hand is an
illustration, not evidence.

Palette and the amber-means-escalation-only rule come from BRANDING.md.
"""

from __future__ import annotations

import hashlib
import html
import math
import os
from pathlib import Path

from src.tools import storage

# BRANDING.md § Palette
DUSK = "#0B1120"
PORCH = "#141E33"
SILL = "#243352"
NEAR = "#3A4A6B"
LAMP = "#FFB454"
HALO = "#FFE2AE"
EMBER = "#E08A34"
CHALK = "#E9EEF7"
DIM = "#8FA0BC"

W, H = 900.0, 380.0
MARGIN = 34.0
MIN_SEP = 30.0          # keeps the field from collapsing into an unreadable clump
CLUSTER_RADIUS = 46.0


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
        for rid in group:
            angle = _rand(rid, "a") * math.tau
            dist = (0.45 + 0.55 * _rand(rid, "d")) * CLUSTER_RADIUS
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
        return HALO, 6.5
    if row["cluster_size"] > 1:
        return NEAR, 5.5      # correlated, deliberately not escalated
    return SILL, 5.0          # silently logged — most of the picture


def _svg(rows: list[dict]) -> str:
    by_id = {r["report_id"]: r for r in rows}
    pos = _layout(rows)

    # Every report an alert covers is lit, not only the ones linked from the
    # report that happened to trigger it. A later report joining the cluster is
    # suppressed rather than re-alerted (storage.alert_coverage), and drawing
    # it dim would show a four-report situation as a three-report one.
    alerted = {r["report_id"] for r in rows if r["covered"]}
    for r in rows:
        if r["action"] == "alert":
            alerted.add(r["report_id"])
            alerted.update(x for x in r["related_ids"] if x in by_id)

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
        title = html.escape(f"{r['zone']} — {r['summary'][:90]}")
        parts.append(
            f"<circle cx='{x:.1f}' cy='{y:.1f}' r='{radius}' fill='{colour}'>"
            f"<title>{title}</title></circle>"
        )

    parts.append("</svg>")
    return "".join(parts)


def _card(row: dict, kind: str) -> str:
    accent = LAMP if kind == "alert" else SILL
    label_colour = LAMP if kind == "alert" else DIM
    kicker = (
        f"▲ Pattern — {row['zone']}" if kind == "alert" else f"Logged — {row['zone']}"
    )
    body = row["message"] if kind == "alert" else row["reasoning"]
    n = row["distinct_reporters"]
    foot = (
        f"cluster {row['cluster_size']} · {n} reporter{'' if n == 1 else 's'} · "
        f"{row['time_span_hours']:.0f}h · z={row['anomaly_score']:.1f}"
    )
    return (
        f"<div class='card' style='border-left-color:{accent}'>"
        f"<p class='kicker' style='color:{label_colour}'>{html.escape(kicker)}</p>"
        f"<p class='body'>{html.escape(body)}</p>"
        f"<p class='foot'>{html.escape(foot)}</p></div>"
    )


def build_html(rows: list[dict]) -> str:
    """The whole page as a string."""
    total = len(rows)
    alerts = [r for r in rows if r["action"] == "alert"]
    declined = [r for r in rows if r["action"] != "alert" and r["cluster_size"] > 1]
    silent = total - len(alerts) - len(declined)

    # One card per alert, plus the strongest genuine decline.
    #
    # "Genuine" excludes anything an alert already covers. A report suppressed
    # as a duplicate of the alert above it is a footnote, and putting it here
    # spends the most valuable slot on the page restating the alert instead of
    # showing the thing the product is actually about — a situation that looked
    # alarming and was deliberately not escalated.
    cards = [_card(r, "alert") for r in alerts]
    genuine = [r for r in declined if not r["covered"]]
    if genuine:
        best = max(genuine, key=lambda r: (r["cluster_size"], r["distinct_reporters"]))
        cards.append(_card(best, "decline"))

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Porchlight — run report</title>
<style>
  :root {{ color-scheme: dark; }}
  * {{ box-sizing: border-box; }}
  body {{ margin:0; background:{DUSK}; color:{CHALK}; padding:3rem 1.5rem 4rem;
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
    line-height:1.6; -webkit-font-smoothing:antialiased; }}
  .wrap {{ max-width:62rem; margin:0 auto; }}
  .eyebrow {{ font-size:.7rem; text-transform:uppercase; letter-spacing:.13em;
    font-weight:600; color:{DIM}; margin:0 0 .8rem; }}
  h1 {{ font-family:Georgia,"Times New Roman",serif; font-weight:400;
    font-size:clamp(2.2rem,6vw,3rem); letter-spacing:-.03em; line-height:1.05;
    margin:0 0 .5rem; }}
  h1 .lit {{ color:{LAMP}; }}
  .tagline {{ font-family:Georgia,serif; font-style:italic; color:{DIM};
    margin:0 0 2.5rem; }}
  .tally {{ font-family:ui-monospace,"Cascadia Code",Consolas,monospace;
    font-size:.86rem; color:{DIM}; margin:0 0 2rem; }}
  .tally b {{ color:{LAMP}; font-weight:600; }}
  .panel {{ background:{PORCH}; border-radius:3px; padding:1.75rem; }}
  svg {{ display:block; width:100%; height:auto; }}
  .legend {{ display:flex; gap:1.5rem; flex-wrap:wrap; font-size:.8rem;
    color:{DIM}; margin:1.25rem 0 0; }}
  .legend span {{ display:inline-flex; align-items:center; gap:.5rem; }}
  .dot {{ width:10px; height:10px; border-radius:50%; display:inline-block; }}
  .cards {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(300px,1fr));
    gap:1rem; margin-top:1.5rem; }}
  .card {{ background:{PORCH}; border-left:3px solid {SILL}; border-radius:2px;
    padding:1.15rem 1.35rem; }}
  .card .kicker {{ font-size:.68rem; text-transform:uppercase; letter-spacing:.12em;
    font-weight:700; margin:0 0 .5rem; }}
  .card .body {{ font-size:.92rem; margin:0 0 .75rem; }}
  .card .foot {{ font-family:ui-monospace,Consolas,monospace; font-size:.73rem;
    color:{DIM}; margin:0; }}
  footer {{ color:{DIM}; font-size:.82rem; margin-top:2.5rem; max-width:46rem; }}
</style></head>
<body><div class="wrap">
  <p class="eyebrow">Run report</p>
  <h1>Porch<span class="lit">light</span></h1>
  <p class="tagline">your friendly neighborhood agent</p>

  <p class="tally">{total} reports · {silent} logged silently · {len(declined)}
     correlated and declined · <b>{len(alerts)} alert{'' if len(alerts) == 1 else 's'}</b></p>

  <div class="panel">
    {_svg(rows)}
    <div class="legend">
      <span><i class="dot" style="background:{SILL}"></i> logged silently</span>
      <span><i class="dot" style="background:{NEAR}"></i> correlated, declined</span>
      <span><i class="dot" style="background:{HALO}"></i> escalated</span>
    </div>
  </div>

  <div class="cards">{''.join(cards)}</div>

  <footer>Generated from a run over the demonstration dataset in
  <code>data/seed_reports.json</code>. Every node is a real report processed by
  the pipeline; positions are derived from report content, not arranged by hand.
  Reports about people are stored only in redacted form.</footer>
</div></body></html>
"""


def write(path: str | Path | None = None) -> Path:
    """Render the current database to a file. Returns the path written."""
    out = Path(path or os.environ.get("FNA_HTML_OUT", "out/report.html"))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build_html(storage.rendered_rows()), encoding="utf-8")
    return out


if __name__ == "__main__":
    import sys

    print(write(sys.argv[1] if len(sys.argv) > 1 else None))
