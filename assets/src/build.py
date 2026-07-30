#!/usr/bin/env python3
"""Generate the blueprint-style SVG art used by the profile README.

Every asset is emitted twice — once per GitHub colour scheme — so the README can
select between them with <picture media="(prefers-color-scheme: dark)">.

Usage:  python3 assets/src/build.py
Output: assets/*.svg
"""

from pathlib import Path

OUT = Path(__file__).resolve().parents[1]

MONO = "ui-monospace, 'SF Mono', SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace"

THEMES = {
    "dark": {
        "paper": "#071626",
        "paper2": "#0b2036",
        "grid": "#1d3a55",
        "gridbold": "#27506f",
        "ink": "#cfe9ff",
        "accent": "#38bdf8",
        "accent2": "#f0a500",
        "muted": "#5d829f",
    },
    "light": {
        "paper": "#eef3f8",
        "paper2": "#e3ebf3",
        "grid": "#c2d4e4",
        "gridbold": "#a3bed4",
        "ink": "#123049",
        "accent": "#0369a1",
        "accent2": "#b45309",
        "muted": "#5b7893",
    },
}


def defs(t, uid, w, h):
    """Grid pattern, wipe clip, and the stylesheet.

    Animation is CSS, not SMIL, and every rule uses `animation-fill-mode: both`
    while the element's *attribute* values describe the FINISHED frame. So where
    animation never runs — the GitHub mobile app, OG-image rasterizers, static
    SVG renderers — the art still shows up complete instead of blank.
    """
    return f"""
  <defs>
    <pattern id="fine{uid}" width="20" height="20" patternUnits="userSpaceOnUse">
      <path d="M20 0H0V20" fill="none" stroke="{t['grid']}" stroke-width=".5" opacity=".55"/>
    </pattern>
    <pattern id="bold{uid}" width="100" height="100" patternUnits="userSpaceOnUse">
      <path d="M100 0H0V100" fill="none" stroke="{t['gridbold']}" stroke-width=".9" opacity=".7"/>
    </pattern>
    <linearGradient id="vig{uid}" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{t['paper2']}"/>
      <stop offset="1" stop-color="{t['paper']}"/>
    </linearGradient>
    <linearGradient id="sweepgrad" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="{t['accent']}" stop-opacity="0"/>
      <stop offset=".5" stop-color="{t['accent']}" stop-opacity=".13"/>
      <stop offset="1" stop-color="{t['accent']}" stop-opacity="0"/>
    </linearGradient>
    <clipPath id="wipe{uid}">
      <rect class="wipe" x="0" y="0" width="{w}" height="{h}"/>
    </clipPath>
  </defs>
  <style>
    .fade {{ animation: fade .5s ease-out both; }}
    .wipe {{ animation: wipe 1.5s cubic-bezier(.2,.7,.2,1) both; }}
    .blink {{ animation: fade .5s ease-out 1.9s both, blink 1.1s step-end 2.4s infinite; }}
    .sweep {{ animation: sweep var(--dur, 8s) cubic-bezier(.45,0,.55,1) infinite; }}
    .flow {{ animation: flow 1.1s linear infinite; }}
    @keyframes fade {{ from {{ opacity: 0; }} }}
    @keyframes wipe {{ from {{ width: 0; }} }}
    @keyframes blink {{ 50% {{ opacity: 0; }} }}
    @keyframes sweep {{ from {{ transform: translateX(0); }} to {{ transform: translateX({w + 60}px); }} }}
    @keyframes flow {{ from {{ stroke-dashoffset: 16; }} to {{ stroke-dashoffset: 0; }} }}
    @media (prefers-reduced-motion: reduce) {{
      .fade, .wipe, .blink, .sweep, .flow {{ animation: none; }}
    }}
  </style>"""


def sheet(t, uid, w, h):
    """Paper, grid, frame and corner registration marks."""
    m = 18
    marks = []
    for cx, cy in ((m + 12, m + 12), (w - m - 12, m + 12), (m + 12, h - m - 12), (w - m - 12, h - m - 12)):
        marks.append(
            f'<g stroke="{t["accent"]}" stroke-width="1" opacity=".65">'
            f'<circle cx="{cx}" cy="{cy}" r="7" fill="none"/>'
            f'<path d="M{cx - 12} {cy}h24M{cx} {cy - 12}v24"/></g>'
        )
    return f"""
  <rect width="{w}" height="{h}" fill="url(#vig{uid})"/>
  <rect width="{w}" height="{h}" fill="url(#fine{uid})"/>
  <rect width="{w}" height="{h}" fill="url(#bold{uid})"/>
  <rect x="{m}" y="{m}" width="{w - 2 * m}" height="{h - 2 * m}" fill="none"
        stroke="{t['gridbold']}" stroke-width="1.4"/>
  <rect x="{m + 6}" y="{m + 6}" width="{w - 2 * m - 12}" height="{h - 2 * m - 12}" fill="none"
        stroke="{t['gridbold']}" stroke-width=".7" opacity=".7"/>
  {''.join(marks)}"""


def txt(x, y, s, fill, size=12, weight=400, ls=1.6, anchor="start", opacity=1, extra="", child=""):
    return (f'<text x="{x}" y="{y}" fill="{fill}" font-family="{MONO}" font-size="{size}" '
            f'font-weight="{weight}" letter-spacing="{ls}" text-anchor="{anchor}" '
            f'opacity="{opacity}"{extra}>{child}{s}</text>')


def anim(delay=0.0, cls="fade"):
    """Attribute pair that schedules a CSS class. Never hides the element."""
    return f' class="{cls}" style="animation-delay:{delay}s"'


def dim_line(t, x1, x2, y, label, size=11):
    """A dimension line: |<---- label ---->|"""
    mid = (x1 + x2) / 2
    return f"""
  <g stroke="{t['accent2']}" stroke-width="1" opacity=".95">
    <path d="M{x1} {y - 7}v14M{x2} {y - 7}v14"/>
    <path d="M{x1} {y}h{x2 - x1}" stroke-dasharray="0"/>
    <path d="M{x1 + 2} {y - 4}l7 4-7 4z" fill="{t['accent2']}" stroke="none"/>
    <path d="M{x2 - 2} {y - 4}l-7 4 7 4z" fill="{t['accent2']}" stroke="none"/>
  </g>
  <rect x="{mid - len(label) * size * 0.36 - 8}" y="{y - 9}" width="{len(label) * size * 0.72 + 16}"
        height="18" fill="{t['paper']}"/>
  {txt(mid, y + 4, label, t['accent2'], size=size, ls=2.4, anchor='middle')}"""


def callout(t, n, x, y, text, lead=42, delay=0.0):
    """Circled index + leader line + annotation, drafting style."""
    return f"""
  <g{anim(delay)}>
    <circle cx="{x}" cy="{y}" r="11" fill="none" stroke="{t['accent']}" stroke-width="1.2"/>
    {txt(x, y + 4, n, t['accent'], size=11, ls=0, anchor='middle')}
    <path d="M{x + 11} {y}h{lead}" stroke="{t['accent']}" stroke-width="1" stroke-dasharray="3 3"/>
    <circle cx="{x + 11 + lead}" cy="{y}" r="2" fill="{t['accent']}"/>
    {txt(x + lead + 22, y + 4, text, t['ink'], size=13, ls=1.4)}
  </g>"""


def title_block(t, x, y, w, rows, delay=1.3):
    """Bottom-right drafting title block."""
    rh = 22
    h = rh * len(rows)
    lines = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{t["paper"]}" fill-opacity=".85" '
             f'stroke="{t["gridbold"]}" stroke-width="1.2"/>']
    for i, (k, v) in enumerate(rows):
        ry = y + rh * i
        if i:
            lines.append(f'<path d="M{x} {ry}h{w}" stroke="{t["gridbold"]}" stroke-width=".7"/>')
        lines.append(f'<path d="M{x + 118} {ry}v{rh}" stroke="{t["gridbold"]}" stroke-width=".7"/>')
        lines.append(txt(x + 10, ry + 15, k, t["muted"], size=10, ls=1.8))
        lines.append(txt(x + 130, ry + 15, v, t["ink"], size=11, ls=1.6, weight=600))
    return f'<g{anim(delay)}>{"".join(lines)}</g>'


def scan(t, w, h, dur="8s"):
    """Slow sweeping highlight — the only looping animation, kept subtle."""
    return f"""
  <g opacity=".5">
    <rect class="sweep" style="--dur:{dur}" x="-90" y="0" width="90" height="{h}" fill="url(#sweepgrad)"/>
  </g>"""


# ---------------------------------------------------------------- header ----

def header(t, uid):
    w, h = 1200, 400
    name = "BRIAN BAZURTO"
    body = f"""
  <g clip-path="url(#wipe{uid})">
    {txt(64, 178, name, 'none', size=74, weight=700, ls=7, extra=f' stroke="{t["accent"]}" stroke-width="1.8"')}
    {txt(64, 178, name, t['ink'], size=74, weight=700, ls=7, opacity=.14)}
  </g>
  {txt(66, 214, "SOFTWARE ENGINEER  /  FLORIDA INTERNATIONAL UNIVERSITY  /  HONORS COLLEGE", t['muted'], size=13, ls=2.2, extra=anim(1.5))}
  <rect class="blink" x="766" y="203" width="9" height="14" fill="{t['accent2']}"/>
  {dim_line(t, 64, 660, 252, "EST. 2023  /  STILL SHIPPING")}
  {callout(t, "1", 812, 118, "AI CODING AGENTS", delay=1.9)}
  {callout(t, "2", 812, 158, "GRAMMAR-BASED FUZZING", delay=2.05)}
  {callout(t, "3", 812, 198, "MOBILE + BACKEND SYSTEMS", delay=2.2)}
  {txt(64, 316, "// currently: teaching machines to break my code before someone else does", t['accent'], size=13, ls=1.2, extra=anim(2.5))}
  {txt(64, 352, "MIAMI, FL  /  25.7617 N  80.1918 W", t['muted'], size=11, ls=2)}
  {title_block(t, 812, 268, 356, [("DWG NO.", "BA-00001"), ("SUBJECT", "PROFILE / README"), ("SCALE", "1:1  ·  SHEET 1 OF 1"), ("REV", "C  ·  MAINTAINED")], delay=2.6)}
  {scan(t, w, h)}"""
    return wrap(t, uid, w, h, body)


# ------------------------------------------------------------- fig. 2 ------

def figure(t, uid):
    """FIG. 2 — the build loop, drawn as a process diagram."""
    w, h = 1200, 300
    steps = [("SPEC", "read + question"), ("AGENT", "draft w/ AI"), ("BUILD", "implement"),
             ("FUZZ", "break it"), ("EVAL", "measure")]
    bw, bh, gap = 186, 74, 34
    x0 = 64
    y = 128
    parts = []
    for i, (k, sub) in enumerate(steps):
        x = x0 + i * (bw + gap)
        d = 0.5 + i * 0.18
        parts.append(f"""
  <g{anim(d)}>
    <rect x="{x}" y="{y}" width="{bw}" height="{bh}" fill="{t['paper']}" fill-opacity=".7"
          stroke="{t['accent']}" stroke-width="1.3"/>
    <path d="M{x} {y + 22}h{bw}" stroke="{t['accent']}" stroke-width=".7" opacity=".5"/>
    {txt(x + 10, y + 16, f"0{i + 1}", t['muted'], size=10, ls=1.6)}
    {txt(x + bw / 2, y + 48, k, t['ink'], size=20, weight=700, ls=3, anchor='middle')}
    {txt(x + bw / 2, y + 65, sub, t['muted'], size=10, ls=1.2, anchor='middle')}
  </g>""")
        if i < len(steps) - 1:
            ax = x + bw
            parts.append(f"""
  <g{anim(d + 0.09)}>
    <path class="flow" d="M{ax + 4} {y + bh / 2}h{gap - 14}" stroke="{t['accent2']}" stroke-width="1.2"
          stroke-dasharray="4 4"/>
    <path d="M{ax + gap - 10} {y + bh / 2 - 5}l8 5-8 5z" fill="{t['accent2']}"/>
  </g>""")
    # feedback arc from EVAL back to SPEC
    xr = x0 + (len(steps) - 1) * (bw + gap) + bw / 2
    parts.append(f"""
  <g{anim(1.55)}>
    <path d="M{xr} {y + bh} v34 H{x0 + bw / 2} v-34" fill="none" stroke="{t['muted']}"
          stroke-width="1.1" stroke-dasharray="5 5"/>
    <path d="M{x0 + bw / 2 - 5} {y + bh + 10}l5-10 5 10z" fill="{t['muted']}"/>
    {txt((x0 + xr) / 2 + bw / 2, y + bh + 52, "FEEDBACK — WHAT BROKE, AND WHY IT BROKE", t['muted'], size=11, ls=2, anchor='middle')}
  </g>""")
    body = f"""
  {txt(64, 66, "FIG. 2  —  HOW I BUILD", t['ink'], size=17, weight=700, ls=3.4)}
  <path d="M64 78h300" stroke="{t['accent']}" stroke-width="1.4"/>
  {txt(64, 96, "iterative loop / every stage assumes the previous one is wrong", t['muted'], size=11, ls=1.4)}
  {''.join(parts)}
  {scan(t, w, h, dur='9s')}"""
    return wrap(t, uid, w, h, body)


# -------------------------------------------------------------- footer -----

def footer(t, uid):
    w, h = 1200, 150
    body = f"""
  {txt(64, 62, "END OF SHEET", t['muted'], size=12, ls=3)}
  <path d="M64 74h1072" stroke="{t['gridbold']}" stroke-width="1"/>
  {txt(64, 104, "DRAWN BY  BRIAN BAZURTO", t['ink'], size=12, ls=1.8)}
  {txt(600, 104, "CHECKED BY  A FUZZER", t['muted'], size=12, ls=1.8, anchor='middle')}
  {txt(1136, 104, "REV C", t['accent'], size=12, ls=1.8, anchor='end')}
  {scan(t, w, h, dur='11s')}"""
    return wrap(t, uid, w, h, body)


def wrap(t, uid, w, h, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
            f'role="img" aria-label="blueprint sheet">'
            f'{defs(t, uid, w, h)}{sheet(t, uid, w, h)}{body}</svg>\n')


ASSETS = {"header": header, "fig-build-loop": figure, "footer": footer}

if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for base, fn in ASSETS.items():
        for mode, theme in THEMES.items():
            uid = f"{base.replace('-', '')}{mode}"
            path = OUT / f"{base}-{mode}.svg"
            path.write_text(fn(theme, uid), encoding="utf-8")
            print(f"wrote {path.relative_to(OUT.parent)}")
