#!/usr/bin/env python3
"""Render FIG. 5 — a 12-month commit-activity graph — in the blueprint palette.

Replaces github-readme-activity-graph, which caps at 90 days: anything larger
is silently ignored and falls back to 31. Drawing it here also means the figure
matches the rest of the sheet instead of being a foreign card.

Input:  the GitHub contributions calendar as JSON on stdin, i.e. the payload of
        user.contributionsCollection.contributionCalendar — {"weeks": [...],
        "totalContributions": n}.
Output: <outdir>/activity-dark.svg and <outdir>/activity-light.svg

Usage:  gh api graphql -f query='...' --jq '...' | python3 assets/src/activity.py dist
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build import THEMES, defs, sheet, txt, anim, scan, wrap  # noqa: E402

W, H = 1200, 300
# plot box
L, R, TOP, BOT = 96, 1140, 116, 232

MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN",
          "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]


def weekly(cal):
    """Collapse the calendar into (iso_date_of_week_start, total) per week."""
    out = []
    for wk in cal.get("weeks", []):
        days = wk.get("contributionDays", [])
        if not days:
            continue
        out.append((days[0]["date"], sum(d["contributionCount"] for d in days)))
    return out


def nice_max(v):
    """Round the y-axis top up to something a human would label."""
    if v <= 5:
        return 5
    for step in (10, 20, 25, 50, 100, 200, 250, 500, 1000):
        if v <= step:
            return step
    return int((v + 999) // 1000 * 1000)


def graph(t, uid, cal):
    pts = weekly(cal)
    total = cal.get("totalContributions", sum(v for _, v in pts))
    peak = max((v for _, v in pts), default=0)
    ymax = nice_max(peak)
    n = len(pts)

    def X(i):
        return L if n < 2 else L + (R - L) * i / (n - 1)

    def Y(v):
        return BOT - (BOT - TOP) * (v / ymax if ymax else 0)

    # ---- y grid + labels
    grid = []
    for frac in (0, 0.5, 1):
        val = round(ymax * frac)
        y = Y(val)
        grid.append(f'<path d="M{L} {y:.1f}H{R}" stroke="{t["gridbold"]}" '
                    f'stroke-width=".7" opacity="{.9 if frac == 0 else .45}"/>')
        grid.append(txt(L - 12, y + 4, str(val), t["muted"], size=10, ls=1, anchor="end"))

    # ---- x labels: first week of each month, skipping any that would collide
    xlab, seen, last_x = [], set(), -1e9
    for i, (date, _) in enumerate(pts):
        mo = int(date[5:7])
        if mo in seen or X(i) - last_x < 62:
            continue
        seen.add(mo)
        last_x = X(i)
        xlab.append(f'<path d="M{X(i):.1f} {BOT}v6" stroke="{t["gridbold"]}" stroke-width=".8"/>')
        xlab.append(txt(X(i), BOT + 20, MONTHS[mo - 1], t["muted"], size=10, ls=1.4, anchor="middle"))

    # ---- area + line
    line = " ".join(f"{'M' if i == 0 else 'L'}{X(i):.1f} {Y(v):.1f}" for i, (_, v) in enumerate(pts))
    area = f"{line} L{X(n - 1):.1f} {BOT} L{L} {BOT} Z" if n else ""

    dots = "".join(
        f'<circle cx="{X(i):.1f}" cy="{Y(v):.1f}" r="2.4" fill="{t["accent2"]}"/>'
        for i, (_, v) in enumerate(pts) if v == peak and peak > 0
    )

    body = f"""
  {txt(64, 60, "FIG. 5  —  COMMIT ACTIVITY / LAST 12 MONTHS", t['ink'], size=17, weight=700, ls=3.4)}
  <path d="M64 72h520" stroke="{t['accent']}" stroke-width="1.4"/>
  {txt(64, 90, f"{total:,} contributions · {n} weeks · peak {peak} in one week", t['muted'], size=11, ls=1.4)}
  <g{anim(0.3)}>
    {''.join(grid)}
    {''.join(xlab)}
    <path d="{area}" fill="{t['accent']}" fill-opacity=".16"/>
    <path d="{line}" fill="none" stroke="{t['accent']}" stroke-width="1.8"
          stroke-linejoin="round" stroke-linecap="round"/>
    {dots}
    <path d="M{L} {TOP}v{BOT - TOP}" stroke="{t['gridbold']}" stroke-width="1"/>
  </g>
  {txt(R, 90, "WEEKLY TOTAL", t['muted'], size=10, ls=1.8, anchor='end')}
  {scan(t, W, H, dur='11s')}"""
    return wrap(t, uid, W, H, body)


def main():
    outdir = Path(sys.argv[1] if len(sys.argv) > 1 else "dist")
    outdir.mkdir(parents=True, exist_ok=True)
    cal = json.load(sys.stdin)
    if not cal.get("weeks"):
        sys.exit("activity: calendar payload has no weeks")
    for mode, theme in THEMES.items():
        path = outdir / f"activity-{mode}.svg"
        path.write_text(graph(theme, f"act{mode}", cal), encoding="utf-8")
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
