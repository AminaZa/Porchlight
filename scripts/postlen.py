"""Character count of each builder post's publishable body.

builder.aws.com caps a post at 3000 characters. The files carry frontmatter,
a working title, tags and a draft note that are *not* part of the post — the
body is everything after the standalone `---` that follows the tags line.
This counts exactly what gets pasted, so the cap is checked against the same
string a human would paste.
"""

from __future__ import annotations

import pathlib
import sys

LIMIT = 3000


def body(text: str) -> str:
    """Everything after the rule that follows the Tags line."""
    _, _, rest = text.partition("**Tags:**")
    _, sep, after = rest.partition("\n---\n")
    if not sep:  # CRLF checkout
        _, sep, after = rest.partition("\r\n---\r\n")
    return after.strip()


def main() -> int:
    paths = sorted(pathlib.Path("posts").glob("builder-post-*.md"))
    if not paths:
        print("no posts found", file=sys.stderr)
        return 1

    worst = 0
    for p in paths:
        n = len(body(p.read_text(encoding="utf-8")))
        over = n - LIMIT
        worst = max(worst, over)
        flag = f"OVER by {over}" if over > 0 else f"ok, {-over} to spare"
        print(f"{p.name:24} {n:>5} chars  {flag}")

    return 1 if worst > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
