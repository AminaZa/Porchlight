"""Verify every published figure against the run that actually produced it.

Run this before recording and again before submitting:

    python scripts/check_claims.py

It reads the live database, derives what is true, and then checks that every
surface a judge will see says the same thing. Exits non-zero on any drift, so
it can gate a commit or a recording session.

**Why this exists.** On 2026-09-02 four separate figures were found to have
drifted from the run they described: the video script quoted the alert as
4 reports / 4 reporters / 36 hours when it fires at 3 / 3 / 13; it paraphrased
four seed reports that the redesigned report page now shows verbatim, so the
same report appeared two ways inside three minutes; the implementation plan
still carried a $0.90/run list-price estimate against a measured $1.90; and the
page header claimed "one street, last night" for a dataset spanning eight zones
and thirty-seven days. Every one of those was written when it was true. None of
them was noticed by a person re-reading the file.

The rule this encodes: **a number that appears on two surfaces can disagree
with itself, so either derive it from the run or check it against the run.**

This does not check prose, tone, or claims that are not numeric. It checks the
figures, the verbatim quotes that go on camera, and the structural guarantees
of the generated page.
"""

from __future__ import annotations

import os
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

os.environ.setdefault("FNA_DB_PATH", "porchlight.db")

from src import render                       # noqa: E402
from src.tools import storage                # noqa: E402

GREEN, RED, YELLOW, DIM, OFF = (
    "\033[32m", "\033[31m", "\033[33m", "\033[2m", "\033[0m"
)
if os.name == "nt" and not os.environ.get("WT_SESSION"):
    # Older Windows consoles render the escapes literally, which is worse than
    # no colour at all.
    GREEN = RED = YELLOW = DIM = OFF = ""

# The default Windows console is cp1252 and this script prints the project's
# own punctuation back at you. Without this it dies on a middot.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):       # already utf-8, or not a real tty
        pass

findings: list[tuple[str, str, str]] = []     # (status, surface, message)


def ok(surface: str, msg: str) -> None:
    findings.append(("ok", surface, msg))


def fail(surface: str, msg: str) -> None:
    findings.append(("fail", surface, msg))


def warn(surface: str, msg: str) -> None:
    findings.append(("warn", surface, msg))


def read(name: str) -> str:
    p = ROOT / name
    return p.read_text(encoding="utf-8") if p.exists() else ""


def _has_number(text: str, value: str) -> str | None:
    """Whether `value` appears in `text` as a number in its own right.

    Guards against the substring trap: "3" is inside "3.5", so a behaviours row
    reading "4 reports ... 3.5 days" once satisfied a check for three reports
    and reported itself green. Found 2026-09-10.
    """
    return re.search(rf"(?<![\d.]){re.escape(value)}(?![\d.])", text)


def plain(text: str) -> str:
    """Markdown emphasis removed and whitespace flattened.

    The script bolds the words it wants on screen -- "There has been **a guy**
    hanging around the **mailboxes**" -- and that is formatting, not a
    paraphrase. Comparing the raw markdown would fail every correctly quoted
    report, which is a checker that cries wolf until nobody runs it.
    """
    return " ".join(re.sub(r"[*_`]", "", text).split())


# --------------------------------------------------------------------------
# What is true, taken from the run rather than from any document.
# --------------------------------------------------------------------------

def facts() -> dict:
    rows = storage.rendered_rows(include_raw=True)
    if not rows:
        print(f"{RED}No rows in {os.environ['FNA_DB_PATH']}. "
              f"Run demo/run_demo.py first.{OFF}")
        raise SystemExit(2)

    counts = {k: sum(r["outcome"] == k for r in rows)
              for k in ("silent", "declined", "suppressed", "alert")}
    alerts = [r for r in rows if r["outcome"] == "alert"]

    # The strongest refusal that is not just a duplicate of an alert -- the
    # same selection the page makes, so the two cannot pick different rows.
    genuine = [r for r in rows
               if r["outcome"] in ("declined", "suppressed") and not r["covered"]]
    decline = (max(genuine, key=lambda r: (r["cluster_size"], r["distinct_reporters"]))
               if genuine else None)

    # The single-reporter refusal is a *different* behaviour from whichever
    # refusal happens to be largest, and it has to be found by what it is rather
    # than by size. On 2026-09-10 those were the same row for the last time: a
    # report regrouped, Birch Ln went 3 -> 4, and the largest decline stopped
    # being the one-person cluster the README row was describing. The check
    # failed loudly, which is the system working -- but it failed by reporting
    # "4 reporters" for a row about a single reporter, which reads as nonsense
    # until you know why.
    solo = [r for r in genuine if r["distinct_reporters"] == 1]
    # Ties on size are real -- run 5 had two three-report one-person clusters.
    # Break on span so the row is deterministic rather than whichever the
    # query happened to return first.
    solo = (max(solo, key=lambda r: (r["cluster_size"], r["time_span_hours"]))
            if solo else None)

    stamps = sorted(r["timestamp"] for r in rows)
    span = (datetime.fromisoformat(stamps[-1])
            - datetime.fromisoformat(stamps[0])).total_seconds() / 86400

    return {
        "rows": rows,
        "total": len(rows),
        "counts": counts,
        "alert": alerts[0] if alerts else None,
        "alerts": alerts,
        "decline": decline,
        "solo": solo,
        "zones": len({r["zone"] for r in rows}),
        "span_days": round(span),
        "never_surfaced": len(rows) - len(alerts),
    }


# --------------------------------------------------------------------------
# Checks
# --------------------------------------------------------------------------

def check_page(f: dict) -> None:
    """The generated page: structural guarantees a judge or a test would hit."""
    page = read("out/report.html")
    if not page:
        fail("out/report.html", "missing -- regenerate before recording")
        return

    if "http://" in page or "https://" in page:
        fail("out/report.html", "contains an external URL; page is not self-contained")
    else:
        ok("out/report.html", "self-contained (no external references)")

    tallies = re.findall(r'<p class="tally">(.*?)</p>', page, re.S)
    if len(tallies) != 1:
        fail("out/report.html", f"expected exactly one tally element, found {len(tallies)}")
    else:
        nums = [int(n) for n in re.findall(r"\d+", tallies[0])]
        c = f["counts"]
        expected = [f["total"], c["silent"], c["declined"]]
        if c["suppressed"]:
            expected.append(c["suppressed"])
        expected.append(c["alert"])
        if nums == expected:
            ok("out/report.html", f"tally matches the run: {expected}")
        else:
            fail("out/report.html",
                 f"tally reads {nums}, the run is {expected} -- regenerate the page")

    # Every report must be drawn, and the marks must add up to the total.
    lit, cov = page.count("'mark lit'"), page.count("'mark cov'")
    plain = page.count("class='mark'")
    if lit + cov + plain == f["total"]:
        ok("out/report.html", f"marks reconcile: {lit} lit + {cov} ringed + {plain} plain "
                              f"= {f['total']}")
    else:
        fail("out/report.html",
             f"marks total {lit + cov + plain}, run has {f['total']} reports")

    nodes = re.findall(r"<circle cx='[\d.]+' cy='[\d.]+' r='[\d.]+' fill='#\w+'", page)
    if len(nodes) == f["total"]:
        ok("out/report.html", f"every one of {f['total']} reports has a node")
    else:
        fail("out/report.html", f"{len(nodes)} nodes drawn for {f['total']} reports")


def _row(text: str, label: str) -> str:
    for line in text.splitlines():
        if label in line:
            return line
    return ""


def check_readme(f: dict) -> None:
    """The three-behaviours table is the most-quoted thing in the project."""
    md = read("README.md")
    if not md:
        fail("README.md", "missing")
        return

    a = f["alert"]
    if a:
        row = _row(md, "The real cluster")
        want = {
            "cluster size": str(a["cluster_size"]),
            "distinct reporters": str(a["distinct_reporters"]),
            "hours": f"{a['time_span_hours']:.0f}",
            "anomaly score": f"{a['anomaly_score']:.1f}",
        }
        if not row:
            fail("README.md", "no 'The real cluster' row found in the behaviours table")
        else:
            missing = [k for k, v in want.items() if v not in row]
            if missing:
                fail("README.md",
                     f"'The real cluster' row is missing {', '.join(missing)} "
                     f"-- run is {want}")
            else:
                ok("README.md", f"real-cluster row matches the run ({want['cluster size']} "
                                f"reports, {want['distinct reporters']} reporters, "
                                f"{want['hours']}h, z={want['anomaly score']})")

    # Two refusals, two rows, checked against the fact each one is about.
    for label, key, note in (("The spread", "decline", "the featured refusal, "
                              "the same one the report page shows"),
                             ("The single reporter", "solo", "the one-person cluster")):
        d = f[key]
        if not d:
            warn("README.md", f"the run has no refusal for the '{label}' row ({note})")
            continue
        row = _row(md, label)
        days = f"{d['time_span_hours'] / 24:.1f}"
        # A whole number of days should be allowed to read as "21 days" in prose
        # rather than "21.0 days". Both are the same fact.
        day_forms = (days, days[:-2]) if days.endswith(".0") else (days,)
        want = {"cluster size": (str(d["cluster_size"]),),
                "reporters": (str(d["distinct_reporters"]),),
                "days": day_forms}
        if not row:
            fail("README.md", f"no '{label}' row found -- {note}")
            continue
        # Plain substring matching lies here: "3" is inside "3.5", so a row
        # reading "4 reports ... 3.5 days" satisfied a check for 3 reports.
        # Require the number to stand alone, not sit inside another one.
        missing = [k for k, vs in want.items()
                   if not any(_has_number(row, v) for v in vs)]
        if missing:
            shown = {k: vs[0] for k, vs in want.items()}
            fail("README.md",
                 f"'{label}' row is missing {', '.join(missing)} -- run is {shown}")
        else:
            ok("README.md", f"'{label}' row matches the run ({d['cluster_size']} "
                            f"reports, {d['distinct_reporters']} reporter(s), {days} days)")

    if str(f["total"]) in md:
        ok("README.md", f"quotes the run size ({f['total']} reports)")
    else:
        warn("README.md", f"does not mention the run size ({f['total']})")


def check_devpost(f: dict) -> None:
    md = read("DEVPOST.md")
    if not md:
        fail("DEVPOST.md", "missing")
        return

    # Anything the Devpost text presents in quotation marks as a neighbour's own
    # words has to be a literal run of some real report. The description and the
    # live-demo page are read minutes apart by the same judge, and the page shows
    # these four verbatim -- so a paraphrase here is a visible contradiction, not
    # a stylistic choice.
    #
    # Found 2026-09-09: the text said "a person hanging around the mailboxes" for
    # a seed that reads "a guy", and "a person waiting around" for "Person
    # waiting". "a guy" is exactly the person-description triage strips, so the
    # paraphrase quietly sanded off the redaction claim's own payoff.
    quoted = re.findall(r'^\s*-\s*"([^"\n]{15,})"\s*$', md, re.MULTILINE)
    if quoted:
        corpus = " || ".join(
            plain(r.get("raw_text") or "").lower() for r in f["rows"]
        )
        stray = [q for q in quoted if plain(q).lower() not in corpus]
        if stray:
            fail("DEVPOST.md",
                 f"{len(stray)} of {len(quoted)} quoted report(s) are not verbatim "
                 f"from any report in the run. First: \"{stray[0][:58]}...\"")
        else:
            ok("DEVPOST.md",
               f"all {len(quoted)} quoted reports are verbatim from the run")

    pend = md.count("⟨PENDING")
    if pend:
        warn("DEVPOST.md", f"{pend} unresolved ⟨PENDING⟩ placeholder(s) -- "
                           f"these must be filled before submitting")
    else:
        ok("DEVPOST.md", "no unresolved placeholders")

    # The "37 of 38" claim is the pitch, so it has to survive a re-run.
    words = {38: "thirty-eight", 37: "thirty-seven", 36: "thirty-six",
             39: "thirty-nine", 35: "thirty-five"}
    n, t = f["never_surfaced"], f["total"]
    phrase = f"{words.get(n, n)} of {words.get(t, t)}"
    if phrase in md.lower():
        ok("DEVPOST.md", f"'{phrase}' matches the run")
    else:
        fail("DEVPOST.md",
             f"cannot find '{phrase}'; the run has {n} of {t} never surfacing")


def check_video(f: dict) -> None:
    """The script is not in the freeze scope, but drift here lands on camera."""
    md = read("VIDEO_SCRIPT.md")
    if not md:
        fail("VIDEO_SCRIPT.md", "missing")
        return

    # The four cluster reports are shown verbatim in §1 and again, from the
    # database, in §3d. A paraphrase in one place is a visible contradiction.
    cluster = [r for r in f["rows"] if r["covered"] or r["outcome"] == "alert"]
    flat = plain(md)
    off = []
    for r in cluster:
        raw = (r.get("raw_text") or "").strip()
        if not raw:
            continue
        # Compare the opening clause; the script wraps lines and may trim the
        # trailing sentence for screen.
        head = plain(raw)[:60]
        if head not in flat:
            off.append(head)
    if not cluster:
        warn("VIDEO_SCRIPT.md", "no escalated cluster in this run to check §1 quotes against")
    elif off:
        fail("VIDEO_SCRIPT.md",
             f"{len(off)} of {len(cluster)} §1 report quotes are not verbatim. "
             f"First mismatch: \"{off[0]}...\"")
    else:
        ok("VIDEO_SCRIPT.md", f"all {len(cluster)} §1 report quotes are verbatim from the run")

    a = f["alert"]
    if a:
        want = [str(a["cluster_size"]), str(a["distinct_reporters"]),
                f"{a['time_span_hours']:.0f}", f"{a['anomaly_score']:.1f}"]
        # §3c is the beat that reads these aloud.
        sec = md.split("### 3c")[-1].split("### 3d")[0] if "### 3c" in md else ""
        missing = [w for w in want if w not in sec]
        if not sec:
            warn("VIDEO_SCRIPT.md", "could not locate §3c to check its figures")
        elif missing:
            fail("VIDEO_SCRIPT.md",
                 f"§3c does not carry {missing} -- the run alerts at "
                 f"{want[0]} reports / {want[1]} reporters / {want[2]}h / z={want[3]}")
        else:
            ok("VIDEO_SCRIPT.md", f"§3c figures match the run ({'/'.join(want)})")


def check_cost() -> None:
    """One measured cost figure, or none. Two is how they disagree."""
    cents = render.COST["per_report_cents"]
    plan = read("IMPLEMENTATION_PLAN.md")
    if f"{cents} cents" in plan or f"{cents} cents" in plan:
        ok("IMPLEMENTATION_PLAN.md", f"cost agrees with src/render.py ({cents}c per report)")
    else:
        fail("IMPLEMENTATION_PLAN.md",
             f"does not carry the measured figure of {cents} cents per report "
             f"that src/render.py publishes")

    stale = re.findall(r"\$0\.90 per full", plan)
    if stale and "Superseded" not in plan:
        fail("IMPLEMENTATION_PLAN.md", "still presents $0.90/run as current")


def check_models() -> None:
    """The submission has to name the models that actually ran."""
    try:
        from src.provider import model_id
        ids = {role: model_id(role) for role in ("triage", "correlation", "escalation")}
    except Exception as exc:                                  # pragma: no cover
        warn("models", f"could not read model ids ({exc.__class__.__name__})")
        return

    names = {}
    for role, ident in ids.items():
        m = re.search(r"claude-(haiku|sonnet|opus)-(\d)-(\d)", ident)
        names[role] = f"{m.group(1).capitalize()} {m.group(2)}.{m.group(3)}" if m else ident

    for surface in ("README.md", "DEVPOST.md", "assets/architecture.html"):
        text = read(surface)
        if not text:
            continue
        missing = [n for n in names.values() if n not in text]
        if missing:
            fail(surface, f"does not name {', '.join(missing)} -- these are the models "
                          f"that produced the run")
        else:
            ok(surface, f"names the models that ran ({', '.join(names.values())})")


def check_holdout() -> None:
    """The holdout number never ships without what it does not prove."""
    h = render.HOLDOUT
    claim = f"{h['passed']} of {h['total']}"
    for surface in ("README.md", "DEVPOST.md"):
        text = read(surface)
        if not text:
            continue
        said = (claim in text
                or f"{h['passed']}/{h['total']}" in text
                or "all twenty" in text.lower())
        caveat = any(phrase in text.lower() for phrase in (
            "zero declines",
            "0 declined",
            "does not show it declining",
            "does not prove",
            "not show the agent refusing",
            "retrieval separated them rather than judgment",
        ))
        if said and caveat:
            ok(surface, f"holdout ({claim}) ships with what it does not prove")
        elif said:
            fail(surface, f"quotes the holdout ({claim}) without stating that it "
                          f"produced zero declines and so does not show a refusal")
        else:
            warn(surface, f"does not mention the holdout result ({claim})")


def main() -> int:
    f = facts()

    print()
    print(f"  Run under test: {DIM}{os.environ['FNA_DB_PATH']}{OFF}")
    c = f["counts"]
    print(f"  {f['total']} reports · {f['zones']} zones · {f['span_days']} days · "
          f"{c['silent']} silent · {c['declined']} declined · "
          f"{c['suppressed']} suppressed · {c['alert']} alert")
    if f["alert"]:
        a = f["alert"]
        print(f"  Alert: {a['cluster_size']} reports · {a['distinct_reporters']} reporters "
              f"· {a['time_span_hours']:.0f}h · z={a['anomaly_score']:.1f} · {a['zone']}")
    print()

    check_page(f)
    check_readme(f)
    check_devpost(f)
    check_video(f)
    check_cost()
    check_models()
    check_holdout()

    width = max(len(s) for _, s, _ in findings) + 2
    for status, surface, msg in findings:
        mark = {"ok": f"{GREEN}pass{OFF}", "fail": f"{RED}FAIL{OFF}",
                "warn": f"{YELLOW}warn{OFF}"}[status]
        print(f"  {mark}  {surface:<{width}} {msg}")

    fails = sum(s == "fail" for s, _, _ in findings)
    warns = sum(s == "warn" for s, _, _ in findings)
    print()
    if fails:
        print(f"  {RED}{fails} figure(s) disagree with the run.{OFF} "
              f"Fix them before recording.")
    else:
        print(f"  {GREEN}Every checked figure matches the run.{OFF}"
              + (f" {warns} warning(s)." if warns else ""))
    print()
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
