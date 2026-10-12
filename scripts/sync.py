#!/usr/bin/env python3
"""Sync HANCORE-linux omarchy palettes → gray theme files.

Reads each `omarchy-*-theme` repo's colors.toml (fetched from GitHub, or
local copies under scripts/upstream/hc-*.toml) and writes one gray theme
JSON per palette into themes/hancore-<name>.json.

Gray theme files are `{ "vars": {...}, "colors": { role: color } }` where a
color is "#rrggbb", an ANSI name, a 0-255 index, "default", or a var name.
Roles we don't emit fall back to the built-in gray palette.

Usage:
    sync.py            # fetch upstream colors.tomls, regenerate themes/
    sync.py --local    # regenerate from scripts/upstream/*.toml only
"""

import json
import re
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UPSTREAM = ROOT / "scripts" / "upstream"
OUT = ROOT / "themes"

REPOS = [
    "aamis", "banish", "batou", "blackgold", "blackmoney", "blackturq",
    "demon", "dos-moos", "greek-noir", "harbor", "harbordark", "inkypinky",
    "kanso", "labra", "lasthorizon", "mechanoonna", "moodpeak", "oxford",
    "oxocarbon", "roseofdune", "ryu", "saga", "sapphire", "shadesofjade",
    "solitude", "thegreek", "turbonite", "velvetnight", "whitegold",
]

HANCORE_SOURCE = "https://github.com/HANCORE-linux/omarchy-{}-theme"
NORD_SOURCE = "https://github.com/nordtheme/nord"

NORD = {
    "nord0": "#2e3440",
    "nord1": "#3b4252",
    "nord2": "#434c5e",
    "nord3": "#4c566a",
    "nord4": "#d8dee9",
    "nord5": "#e5e9f0",
    "nord6": "#eceff4",
    "nord7": "#8fbcbb",
    "nord8": "#88c0d0",
    "nord9": "#81a1c1",
    "nord10": "#5e81ac",
    "nord11": "#bf616a",
    "nord12": "#d08770",
    "nord13": "#ebcb8b",
    "nord14": "#a3be8c",
    "nord15": "#b48ead",
}


def hex2rgb(h):
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


def rgb2hex(rgb):
    return "#{:02x}{:02x}{:02x}".format(*(round(c) for c in rgb))


def mix(a, b, t):
    return tuple(x + (y - x) * t for x, y in zip(a, b))


def lum(rgb):
    return (0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]) / 255


def parse_colors_toml(text):
    try:
        return tomllib.loads(text)
    except tomllib.TOMLDecodeError:
        out = {}
        for line in text.splitlines():
            m = re.match(r'^\s*([A-Za-z0-9_]+)\s*=\s*"([^"]*)"', line)
            if m:
                out[m.group(1)] = m.group(2)
        return out


def fetch(name):
    raw = subprocess.run(
        ["gh", "api", f"repos/HANCORE-linux/omarchy-{name}-theme/contents/colors.toml",
         "--jq", ".content"],
        check=True, capture_output=True, text=True,
    ).stdout
    import base64
    return base64.b64decode(raw).decode()


def convert(name, src, source_url):
    get = lambda k: src.get(k, "").strip() or None

    bg = hex2rgb(get("background") or "#161616")
    fg = hex2rgb(get("foreground") or "#e1e1e1")
    dark = (get("mode") == "dark") if get("mode") else lum(bg) < 0.45
    pole = (255, 255, 255) if dark else (0, 0, 0)

    def col(key, fallback):
        v = get(key)
        return hex2rgb(v) if v else fallback

    muted = col("muted", col("color8", mix(bg, fg, 0.4)))
    sel_bg = col("selection_background", col("selection", col("accent", muted)))
    sel_fg = col("selection_foreground", pole)
    lighter = col("lighter_background", mix(bg, fg, 0.07))
    light_fg = col("light_foreground", mix(fg, pole, 0.18))
    accent = col("accent", mix(muted, fg, 0.5))

    red = col("red", col("color1", (239, 68, 68)))
    green = col("green", col("color2", (74, 222, 128)))
    yellow = col("yellow", col("color3", (250, 204, 21)))
    blue = col("blue", col("color4", (59, 130, 246)))
    magenta = col("magenta", col("color5", red))
    cyan = col("cyan", col("color6", blue))
    orange = col("orange", yellow)
    bright_red = col("bright_red", mix(red, pole, 0.3))

    vars_ = {
        "bg": rgb2hex(bg), "fg": rgb2hex(fg), "muted": rgb2hex(muted),
        "sel_bg": rgb2hex(sel_bg), "sel_fg": rgb2hex(sel_fg),
        "lighter": rgb2hex(lighter), "light_fg": rgb2hex(light_fg),
        "accent": rgb2hex(accent),
        "red": rgb2hex(red), "green": rgb2hex(green), "yellow": rgb2hex(yellow),
        "blue": rgb2hex(blue), "magenta": rgb2hex(magenta), "cyan": rgb2hex(cyan),
        "orange": rgb2hex(orange), "bright_red": rgb2hex(bright_red),
    }
    h = lambda c: rgb2hex(c)

    colors = {
        "surface_bg": "bg",
        "raised_bg": h(mix(bg, lighter, 0.6)),
        "input_bg": "lighter",
        "on_selection": "sel_fg",
        "chip_bg": "sel_bg",
        "text_faint": h(mix(bg, muted, 0.55)),
        "text_dim": "muted",
        "text_muted": h(mix(muted, fg, 0.45)),
        "text_soft": h(mix(muted, fg, 0.75)),
        "text_body": "fg",
        "text_bright": "light_fg",
        "accent": "accent",
        "accent_soft": h(mix(accent, pole, 0.22)),
        "success": "green",
        "error": "red",
        "error_soft": "bright_red",
        "rose": h(mix(magenta, pole, 0.3)),
        "info": "blue",
        "tool_accent": "green",
        "tool_path": "orange",
        "tool_command": "yellow",
        "tool_dim": h(mix(muted, bg, 0.35)),
        "diff_add_fg": "green",
        "diff_add_bg": h(mix(bg, green, 0.13)),
        "diff_del_fg": "red",
        "diff_del_bg": h(mix(bg, red, 0.15)),
        "diff_gutter": h(mix(muted, bg, 0.35)),
        "cache_hit": h(mix(muted, green, 0.5)),
        "ctx_system": h(mix(muted, fg, 0.55)),
        "ctx_context": "green",
        "ctx_tools": "cyan",
        "ctx_skills": "yellow",
        "ctx_messages": "orange",
        "ctx_free": h(mix(muted, bg, 0.3)),
        "shimmer_base": h(mix(muted, fg, 0.55)),
        "bezel_hi": h(mix(bg, fg, 0.42)),
        "bezel_mid": h(mix(bg, fg, 0.26)),
        "bezel_lo": h(mix(bg, fg, 0.12)),
        "hue_red": "red",
        "hue_orange": "orange",
        "hue_yellow": "yellow",
        "hue_green": "green",
        "hue_cyan": "cyan",
        "hue_blue": "blue",
        "hue_magenta": "magenta",
    }
    doc = {
        "_source": source_url,
        "_mode": "dark" if dark else "light",
        "vars": vars_,
        "colors": colors,
    }
    return json.dumps(doc, indent=2) + "\n"


def nord_sources():
    n = NORD
    base = {
        "mode": "dark",
        "background": n["nord0"],
        "lighter_background": n["nord1"],
        "foreground": n["nord4"],
        "light_foreground": n["nord6"],
        "muted": "#616e88",
        "accent": n["nord8"],
        "selection_background": n["nord2"],
        "selection_foreground": n["nord0"],
        "red": n["nord11"],
        "orange": n["nord12"],
        "yellow": n["nord13"],
        "green": n["nord14"],
        "magenta": n["nord15"],
        "blue": n["nord9"],
        "cyan": n["nord7"],
        "color0": n["nord1"],
        "color1": n["nord11"],
        "color2": n["nord14"],
        "color3": n["nord13"],
        "color4": n["nord9"],
        "color5": n["nord15"],
        "color6": n["nord8"],
        "color7": n["nord5"],
        "color8": n["nord3"],
        "color9": n["nord11"],
        "color10": n["nord14"],
        "color11": n["nord13"],
        "color12": n["nord9"],
        "color13": n["nord15"],
        "color14": n["nord7"],
        "color15": n["nord6"],
    }
    darker = dict(base, background="#242933", lighter_background=n["nord0"])
    shade = lambda c: rgb2hex(mix(hex2rgb(c), hex2rgb(n["nord0"]), 0.25))
    light = {
        "mode": "light",
        "background": n["nord6"],
        "lighter_background": n["nord5"],
        "foreground": n["nord0"],
        "light_foreground": "#242933",
        "muted": "#7b88a1",
        "accent": n["nord10"],
        "selection_background": n["nord4"],
        "selection_foreground": n["nord6"],
        "red": shade(n["nord11"]),
        "orange": shade(n["nord12"]),
        "yellow": shade(n["nord13"]),
        "green": shade(n["nord14"]),
        "magenta": shade(n["nord15"]),
        "blue": n["nord10"],
        "cyan": shade(n["nord7"]),
    }
    return {"nord": base, "nord-darker": darker, "nord-light": light}


def main():
    local_only = "--local" in sys.argv
    OUT.mkdir(exist_ok=True)
    UPSTREAM.mkdir(exist_ok=True)
    for name in REPOS:
        cache = UPSTREAM / f"hc-{name}.toml"
        if local_only or cache.exists():
            text = cache.read_text()
        else:
            print(f"fetch {name}")
            text = fetch(name)
            cache.write_text(text)
        src = parse_colors_toml(text)
        out = OUT / f"{name}.json"
        out.write_text(convert(name, src, HANCORE_SOURCE.format(name)))
        print(f"wrote {out.name}")
    for name, src in nord_sources().items():
        out = OUT / f"{name}.json"
        out.write_text(convert(name, src, NORD_SOURCE))
        print(f"wrote {out.name}")
    print(f"{len(REPOS) + 3} themes → {OUT}")


if __name__ == "__main__":
    main()
