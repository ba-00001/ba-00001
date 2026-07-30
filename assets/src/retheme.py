#!/usr/bin/env python3
"""Recolour an arcade contribution SVG into the blueprint palette.

The upstream action only offers four named themes, none of which match this
sheet. It is, however, deterministic about colour: cells use the standard
GitHub ramp, maze walls are #000000, chrome text is grey, and the player is
`fill="yellow"`. That is a small enough surface to remap exactly.

Doing the remap here also routes around an upstream bug: the Pac-Man run writes
its light SVG and then exits silently without ever producing the dark one
(Breakout produces both). Since every game reliably emits the *light* file,
both output variants are derived from that one source.

Usage:  python3 assets/src/retheme.py <source-light.svg> <out-prefix>
        -> <out-prefix>-dark.svg, <out-prefix>-light.svg
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build import THEMES  # noqa: E402

# GitHub light palette -> semantic role
ROLES = {
    "#ebedf0": "empty",
    "#9be9a8": "l1",
    "#40c463": "l2",
    "#30a14e": "l3",
    "#216e39": "l4",
    "#000000": "wall",
    "#57606a": "muted",
    "#808080": "muted",
    "#ffffff": "paper",   # the card background, not text
}

def palette(t, mode):
    ramp = ([t["paper2"], t["grid"], t["gridbold"], t["accent"], "#7dd3fc"] if mode == "dark"
            else [t["paper2"], t["grid"], t["gridbold"], t["accent"], "#075985"])
    return {
        "empty": ramp[0], "l1": ramp[1], "l2": ramp[2], "l3": ramp[3], "l4": ramp[4],
        "wall": t["gridbold"], "muted": t["muted"], "ink": t["ink"],
        "paper": t["paper"], "player": t["accent2"],
    }


def retheme(svg, t, mode):
    pal = palette(t, mode)
    for src, role in ROLES.items():
        dst = pal[role]
        svg = svg.replace(src, dst).replace(src.upper(), dst)
    return svg.replace('fill="yellow"', f'fill="{pal["player"]}"')


def main():
    if len(sys.argv) != 3:
        sys.exit("usage: retheme.py <source-light.svg> <out-prefix>")
    src = Path(sys.argv[1])
    if not src.is_file():
        sys.exit(f"retheme: {src} not found")
    raw = src.read_text(encoding="utf-8")
    for mode, theme in THEMES.items():
        out = Path(f"{sys.argv[2]}-{mode}.svg")
        out.write_text(retheme(raw, theme, mode), encoding="utf-8")
        print(f"wrote {out} ({out.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
