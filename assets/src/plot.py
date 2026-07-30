#!/usr/bin/env python3
"""Render FIG. 6 — the contribution grid drawn by a plotter pen.

A vertical pen head sweeps left to right across the last 53 weeks, and each
week's column inks in as the head passes it. One-shot, not looping: the finished
frame is the complete grid, which is also what a renderer that ignores animation
shows (see the contract in build.py).

Input:  "YYYY-MM-DD <count>" lines on stdin (same feed as activity.py).
Output: <outdir>/plot-dark.svg and <outdir>/plot-light.svg

Usage:  ... | python3 assets/src/plot.py dist
"""

import datetime as dt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build import THEMES, defs, sheet, txt, anim, wrap  # noqa: E402

W, H = 1200, 322
CELL, GAP = 15.0, 3.4
WEEKS = 53
GX, GY = 96.0, 116.0          # grid origin
SWEEP = 5.6                   # seconds for the pen to cross the sheet

MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN",
          "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]


def read_days(stream):
    days = {}
    for raw in stream:
        parts = raw.split()
        if len(parts) != 2:
            continue
        try:
            days[dt.date.fromisoformat(parts[0])] = int(parts[1])
        except ValueError:
            continue
    return days


def build_grid(days):
    """Columns of 7 (Sun..Sat) covering the last WEEKS weeks, GitHub-style."""
    if not days:
        return [], None
    # anchor on the last day that actually has a contribution — the feed covers
    # whole calendar years, so max(days) would be a zero-filled future date and
    # the grid would trail off into empty months
    active = [d for d, v in days.items() if v > 0]
    if not active:
        return [], None
    last = max(active)
    # end on the Saturday of the final week so columns are whole
    end = last + dt.timedelta(days=(5 - last.weekday()) % 7 + 1)
    start = end - dt.timedelta(weeks=WEEKS) + dt.timedelta(days=1)

    cols = []
    d = start
    while d < end:
        col = []
        for _ in range(7):
            col.append((d, days.get(d, 0)))
            d += dt.timedelta(days=1)
        cols.append(col)
    return cols, start


def levels(cols):
    """Map counts to 0-4. Thresholds from the non-zero distribution, so an
    unusually busy day cannot flatten everything else into level 1."""
    vals = sorted(v for col in cols for _, v in col if v > 0)
    if not vals:
        return lambda v: 0
    q = [vals[int(len(vals) * f)] for f in (0.25, 0.55, 0.85)]

    def level(v):
        if v <= 0:
            return 0
        if v <= q[0]:
            return 1
        if v <= q[1]:
            return 2
        if v <= q[2]:
            return 3
        return 4
    return level


def ramp(t):
    """Five-step blueprint ramp: empty grid -> full cyan."""
    return [t["paper2"], t["grid"], t["gridbold"], t["accent"], t["accent2"]]


def graph(t, uid, cols):
    level = levels(cols)
    swatch = ramp(t)
    gw = WEEKS * (CELL + GAP) - GAP
    total = sum(v for col in cols for _, v in col)
    active = sum(1 for col in cols for _, v in col if v > 0)

    cells, ticks, seen = [], [], set()
    for i, col in enumerate(cols):
        x = GX + i * (CELL + GAP)
        # a column inks when the pen head reaches it
        delay = round(0.25 + SWEEP * i / max(WEEKS - 1, 1), 3)
        for j, (date, v) in enumerate(col):
            y = GY + j * (CELL + GAP)
            lv = level(v)
            cells.append(
                f'<rect class="fade" style="animation-delay:{delay}s" x="{x:.1f}" y="{y:.1f}" '
                f'width="{CELL}" height="{CELL}" rx="1.5" fill="{swatch[lv]}" '
                f'stroke="{t["gridbold"]}" stroke-width=".5" stroke-opacity=".5"/>'
            )
        first = col[0][0]
        if first.month not in seen and first.day <= 7:
            seen.add(first.month)
            ticks.append(txt(x + CELL / 2, GY + 7 * (CELL + GAP) + 14,
                             MONTHS[first.month - 1], t["muted"], size=9.5, ls=1, anchor="middle"))

    # weekday guides on the left
    wd = "".join(
        txt(GX - 10, GY + j * (CELL + GAP) + CELL - 3, lbl, t["muted"], size=8.5, ls=.6, anchor="end")
        for j, lbl in ((0, "SUN"), (2, "TUE"), (4, "THU"), (6, "SAT"))
    )

    # legend
    lx = GX + gw - 5 * (CELL + GAP) - 46
    ly = GY + 7 * (CELL + GAP) + 26   # own row, clear of the month ticks
    legend = [txt(lx - 8, ly + 10, "LESS", t["muted"], size=9, ls=1, anchor="end")]
    for k, c in enumerate(swatch):
        legend.append(f'<rect x="{lx + k * (CELL + GAP):.1f}" y="{ly}" width="{CELL}" height="{CELL}" '
                      f'rx="1.5" fill="{c}" stroke="{t["gridbold"]}" stroke-width=".5" stroke-opacity=".5"/>')
    legend.append(txt(lx + 5 * (CELL + GAP) + 4, ly + 10, "MORE", t["muted"], size=9, ls=1))

    # the pen head: a full-height rule with a crosshair, sweeping once
    pen_h = 7 * (CELL + GAP)
    pen = f"""
  <g class="pen">
    <path d="M0 {GY - 14}v{pen_h + 22}" stroke="{t['accent2']}" stroke-width="1.2"/>
    <circle cx="0" cy="{GY - 20}" r="5.5" fill="none" stroke="{t['accent2']}" stroke-width="1.3"/>
    <path d="M-9 {GY - 20}h18M0 {GY - 29}v18" stroke="{t['accent2']}" stroke-width=".9" opacity=".85"/>
  </g>"""

    style = f"""
  <style>
    .pen {{
      animation: pensweep {SWEEP}s cubic-bezier(.42,0,.58,1) .25s both,
                 penout .5s ease-in {SWEEP + .25}s both;
    }}
    @keyframes pensweep {{
      from {{ transform: translateX({GX:.1f}px); }}
      to   {{ transform: translateX({GX + gw:.1f}px); }}
    }}
    @keyframes penout {{ to {{ opacity: 0; }} }}
    @media (prefers-reduced-motion: reduce) {{ .pen {{ animation: none; opacity: 0; }} }}
  </style>"""

    body = f"""
  {txt(64, 60, "FIG. 6  —  CONTRIBUTION PLOT / PEN PATH", t['ink'], size=17, weight=700, ls=3.4)}
  <path d="M64 72h500" stroke="{t['accent']}" stroke-width="1.4"/>
  {txt(64, 92, f"{WEEKS} weeks · {total:,} contributions · {active} active days", t['muted'], size=11, ls=1.4)}
  {txt(1136, 92, "TOOL T1 · ONE PASS", t['muted'], size=10, ls=1.8, anchor='end')}
  {style}
  <g{anim(0.1)}>{wd}</g>
  {''.join(cells)}
  <g{anim(SWEEP)}>{''.join(ticks)}{''.join(legend)}</g>
  {pen}"""
    return wrap(t, uid, W, H, body)


def main():
    outdir = Path(sys.argv[1] if len(sys.argv) > 1 else "dist")
    outdir.mkdir(parents=True, exist_ok=True)
    cols, start = build_grid(read_days(sys.stdin))
    if not cols:
        sys.exit("plot: no contribution days on stdin")
    for mode, theme in THEMES.items():
        path = outdir / f"plot-{mode}.svg"
        path.write_text(graph(theme, f"plot{mode}", cols), encoding="utf-8")
        print(f"wrote {path} ({len(cols)} weeks from {start})")


if __name__ == "__main__":
    main()
