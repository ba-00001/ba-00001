#!/usr/bin/env python3
"""Render the contribution-streak card from the contributions calendar.

Replaces DenverCoder1/github-readme-streak-stats, which reported 9,617 total
contributions, a 12-day current streak and an 18-day longest streak for this
account on 2026-07-30. The calendar API says 2,591 / 3 / 6, and FIG. 5 — built
from that same feed — agrees with the calendar. Rather than publish a number
the rest of the page contradicts, the card is computed here from the one
source of truth.

Input:  "YYYY-MM-DD <count>" lines on stdin (same feed as activity.py/plot.py).
Output: <outdir>/streak-dark.svg and <outdir>/streak-light.svg

Usage:  ... | python3 assets/src/streak.py dist
"""

import datetime as dt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build import MONO, THEMES, txt, anim  # noqa: E402

W, H = 495, 195
MON = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN",
       "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]


def fmt(d):
    return f"{MON[d.month - 1]} {d.day}, {d.year}"


def span(a, b):
    """Drop the repeated year when a range sits inside one."""
    if a.year == b.year:
        return f"{MON[a.month - 1]} {a.day} – {MON[b.month - 1]} {b.day}, {b.year}"
    return f"{fmt(a)} – {fmt(b)}"


def stats(days):
    active = {d for d, v in days.items() if v > 0}
    if not active:
        return None
    first, last = min(active), max(active)

    run = 0
    run_start = None
    spans = []
    d = first
    while d <= last:
        if d in active:
            run += 1
            if run_start is None:
                run_start = d
        else:
            if run:
                spans.append((run, run_start, d - dt.timedelta(days=1)))
            run, run_start = 0, None
        d += dt.timedelta(days=1)
    if run:
        spans.append((run, run_start, last))

    best, bs, be = max(spans, key=lambda s: s[0])

    # Current streak runs back from the most recent active day. GitHub's own
    # card treats "today with nothing yet" as still live, so the walk starts at
    # the last active day rather than at today's date.
    cur, d = 0, last
    while d in active:
        cur += 1
        d -= dt.timedelta(days=1)
    cur_start = last - dt.timedelta(days=cur - 1)

    return {
        "total": sum(days.values()),
        "first": first, "last": last,
        "cur": cur, "cur_start": cur_start,
        "best": best, "best_start": bs, "best_end": be,
    }


def card(t, s):
    third = W / 3
    cx = W / 2

    def panel(x, big, label, sub, delay, color=None):
        return f"""
  <g{anim(delay)}>
    {txt(x, 78, big, color or t['ink'], size=34, weight=700, ls=1, anchor='middle')}
    {txt(x, 104, label, t['muted'], size=10, ls=2, anchor='middle')}
    {txt(x, 126, sub, t['muted'], size=8.5, ls=.8, anchor='middle', opacity=.85)}
  </g>"""

    ring_r = 30
    circ = 2 * 3.14159 * ring_r
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="contribution streak">
  <defs>
    <pattern id="sgrid" width="20" height="20" patternUnits="userSpaceOnUse">
      <path d="M20 0H0V20" fill="none" stroke="{t['grid']}" stroke-width=".5" opacity=".5"/>
    </pattern>
  </defs>
  <style>
    .fade {{ animation: fade .5s ease-out both; }}
    @keyframes fade {{ from {{ opacity: 0; }} }}
    .ring {{ stroke-dasharray: {circ:.1f}; animation: draw 1.1s cubic-bezier(.2,.7,.2,1) .35s both; }}
    @keyframes draw {{ from {{ stroke-dashoffset: {circ:.1f}; }} to {{ stroke-dashoffset: 0; }} }}
    @media (prefers-reduced-motion: reduce) {{ .fade, .ring {{ animation: none; }} }}
  </style>
  <rect width="{W}" height="{H}" fill="{t['paper']}"/>
  <rect width="{W}" height="{H}" fill="url(#sgrid)"/>
  <rect x=".7" y=".7" width="{W - 1.4}" height="{H - 1.4}" fill="none"
        stroke="{t['gridbold']}" stroke-width="1.4"/>
  <path d="M{third} 26V{H - 26}M{third * 2} 26V{H - 26}" stroke="{t['gridbold']}"
        stroke-width=".8" opacity=".7"/>
  {panel(third / 2, f"{s['total']:,}", "TOTAL CONTRIBUTIONS", f"SINCE {fmt(s['first'])}", .25)}
  <g{anim(.35)}>
    <circle cx="{cx}" cy="72" r="{ring_r}" fill="none" stroke="{t['gridbold']}" stroke-width="4" opacity=".55"/>
    <circle class="ring" cx="{cx}" cy="72" r="{ring_r}" fill="none" stroke="{t['accent']}"
            stroke-width="4" stroke-linecap="round" transform="rotate(-90 {cx} 72)"/>
    {txt(cx, 82, str(s['cur']), t['ink'], size=30, weight=700, ls=0, anchor='middle')}
    {txt(cx, 122, "CURRENT STREAK", t['accent'], size=10, ls=2, anchor='middle')}
    {txt(cx, 140, span(s['cur_start'], s['last']), t['muted'], size=8.5, ls=.8, anchor='middle', opacity=.85)}
  </g>
  {panel(third * 2.5, str(s['best']), "LONGEST STREAK", span(s['best_start'], s['best_end']), .45)}
  {txt(W / 2, 176, "COMPUTED FROM THE CONTRIBUTIONS CALENDAR", t['muted'], size=7.5, ls=1.4, anchor='middle', opacity=.6)}
</svg>
"""


def main():
    outdir = Path(sys.argv[1] if len(sys.argv) > 1 else "dist")
    outdir.mkdir(parents=True, exist_ok=True)
    days = {}
    for raw in sys.stdin:
        p = raw.split()
        if len(p) == 2:
            try:
                days[dt.date.fromisoformat(p[0])] = int(p[1])
            except ValueError:
                pass
    s = stats(days)
    if not s:
        sys.exit("streak: no contributions on stdin")
    for mode, theme in THEMES.items():
        path = outdir / f"streak-{mode}.svg"
        path.write_text(card(theme, s), encoding="utf-8")
        print(f"wrote {path}  total={s['total']:,} current={s['cur']} longest={s['best']}")


if __name__ == "__main__":
    main()
