#!/usr/bin/env python3
"""Render FIG. 5 — commit activity per month, across the whole history.

Why monthly-since-joining rather than the obvious "last 12 months":

- The activity-graph service this replaced caps at 90 days. `days=180`/`365`
  are accepted and silently ignored, falling back to 31.
- A year of *weekly* points is mostly flat with a few spikes, which reads as
  "not much happening". The same data bucketed *monthly* over the full history
  has real structure, and the peaks land on labelled months you can point at.
- The peaks are not cherry-picked. Every month between the first and last
  contribution is plotted, quiet ones included: dropping the flat stretches
  would put non-adjacent months side by side and draw a line between them,
  which claims a continuity that isn't there. The top months are *annotated*
  instead, which gets the same emphasis honestly.

Input:  "YYYY-MM-DD <count>" lines on stdin (one per day, any order).
Output: <outdir>/activity-dark.svg and <outdir>/activity-light.svg

Usage:  ... | python3 assets/src/activity.py dist
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build import THEMES, defs, sheet, txt, anim, scan, wrap  # noqa: E402

W, H = 1200, 320
L, R, TOP, BOT = 96, 1140, 118, 224

MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN",
          "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
PEAKS_ANNOTATED = 3


def read_months(stream):
    """Aggregate day lines into an ordered [(YYYY, MM, total)] series.

    Trimmed to the first and last month that actually contain a contribution,
    so the chart neither starts on empty pre-signup months nor runs into the
    unwritten rest of the current year.
    """
    totals = {}
    for raw in stream:
        parts = raw.split()
        if len(parts) != 2:
            continue
        date, count = parts
        try:
            y, m = int(date[0:4]), int(date[5:7])
            totals[(y, m)] = totals.get((y, m), 0) + int(count)
        except ValueError:
            continue
    if not totals:
        return []

    active = sorted(k for k, v in totals.items() if v > 0)
    if not active:
        return []
    (y0, m0), (y1, m1) = active[0], active[-1]

    series, y, m = [], y0, m0
    while (y, m) <= (y1, m1):
        series.append((y, m, totals.get((y, m), 0)))
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return series


def nice_max(v):
    if v <= 5:
        return 5
    for step in (10, 20, 25, 50, 100, 200, 250, 500, 1000, 2000):
        if v <= step:
            return step
    return int((v + 999) // 1000 * 1000)


def graph(t, uid, series):
    n = len(series)
    vals = [v for _, _, v in series]
    total, peak = sum(vals), max(vals)
    ymax = nice_max(peak)

    def X(i):
        return L if n < 2 else L + (R - L) * i / (n - 1)

    def Y(v):
        return BOT - (BOT - TOP) * (v / ymax if ymax else 0)

    # ---- y grid
    grid = []
    for frac in (0, 0.5, 1):
        val = round(ymax * frac)
        y = Y(val)
        grid.append(f'<path d="M{L} {y:.1f}H{R}" stroke="{t["gridbold"]}" '
                    f'stroke-width=".7" opacity="{.9 if frac == 0 else .4}"/>')
        grid.append(txt(L - 12, y + 4, str(val), t["muted"], size=10, ls=1, anchor="end"))

    # ---- x axis: month row, then a year row that only prints on change
    step = 1 if n <= 16 else (2 if n <= 30 else 3)
    xlab = []
    for i, (y, m, _) in enumerate(series):
        if i % step and i != n - 1:
            continue
        xlab.append(f'<path d="M{X(i):.1f} {BOT}v5" stroke="{t["gridbold"]}" stroke-width=".8"/>')
        xlab.append(txt(X(i), BOT + 18, MONTHS[m - 1], t["muted"], size=9.5, ls=1, anchor="middle"))

    years = []
    for i, (y, m, _) in enumerate(series):
        if i and series[i - 1][0] == y:
            continue
        # year divider + label, sitting under the month row
        years.append(f'<path d="M{X(i):.1f} {TOP}V{BOT + 24}" stroke="{t["gridbold"]}" '
                     f'stroke-width=".8" stroke-dasharray="3 4" opacity=".75"/>')
        span_end = next((X(j) for j in range(i + 1, n) if series[j][0] != y), X(n - 1))
        years.append(txt((X(i) + span_end) / 2, BOT + 40, str(y), t["accent"],
                         size=12, weight=700, ls=3, anchor="middle"))

    # ---- line + area
    line = " ".join(f"{'M' if i == 0 else 'L'}{X(i):.1f} {Y(v):.1f}"
                    for i, (_, _, v) in enumerate(series))
    area = f"{line} L{X(n - 1):.1f} {BOT} L{L} {BOT} Z"

    # ---- annotate the biggest months
    top = sorted(range(n), key=lambda i: series[i][2], reverse=True)[:PEAKS_ANNOTATED]
    marks = []
    for i in sorted(top):
        y, m, v = series[i]
        px, py = X(i), Y(v)
        anchor = "start" if px < L + 80 else ("end" if px > R - 80 else "middle")
        dx = 6 if anchor == "start" else (-6 if anchor == "end" else 0)
        marks.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="3.4" fill="{t["accent2"]}"/>')
        marks.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="7" fill="none" '
                     f'stroke="{t["accent2"]}" stroke-width="1" opacity=".55"/>')
        marks.append(txt(px + dx, py - 14, str(v), t["accent2"], size=12, weight=700,
                         ls=1, anchor=anchor))
        marks.append(txt(px + dx, py - 27, f"{MONTHS[m - 1]} {y}", t["muted"], size=9,
                         ls=1.2, anchor=anchor))

    first, last = series[0], series[-1]
    span = (f"{MONTHS[first[1] - 1]} {first[0]} – {MONTHS[last[1] - 1]} {last[0]}")

    body = f"""
  {txt(64, 60, "FIG. 5  —  COMMIT ACTIVITY / BY MONTH", t['ink'], size=17, weight=700, ls=3.4)}
  <path d="M64 72h470" stroke="{t['accent']}" stroke-width="1.4"/>
  {txt(64, 92, f"{span} · {total:,} contributions · busiest month {peak}", t['muted'], size=11, ls=1.4)}
  {txt(R, 92, "MONTHLY TOTAL", t['muted'], size=10, ls=1.8, anchor='end')}
  <g{anim(0.3)}>
    {''.join(grid)}
    {''.join(years)}
    {''.join(xlab)}
    <path d="{area}" fill="{t['accent']}" fill-opacity=".16"/>
    <path d="{line}" fill="none" stroke="{t['accent']}" stroke-width="1.8"
          stroke-linejoin="round" stroke-linecap="round"/>
    {''.join(marks)}
    <path d="M{L} {TOP}v{BOT - TOP}" stroke="{t['gridbold']}" stroke-width="1"/>
  </g>
  {scan(t, W, H, dur='11s')}"""
    return wrap(t, uid, W, H, body)


def main():
    outdir = Path(sys.argv[1] if len(sys.argv) > 1 else "dist")
    outdir.mkdir(parents=True, exist_ok=True)
    series = read_months(sys.stdin)
    if len(series) < 2:
        sys.exit("activity: not enough months with contributions to plot")
    for mode, theme in THEMES.items():
        path = outdir / f"activity-{mode}.svg"
        path.write_text(graph(theme, f"act{mode}", series), encoding="utf-8")
        print(f"wrote {path} ({len(series)} months)")


if __name__ == "__main__":
    main()
