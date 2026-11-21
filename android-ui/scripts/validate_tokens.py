#!/usr/bin/env python3
"""Color token validator and adjuster.

Takes one or more user-chosen colors, checks WCAG contrast across light/dark
schemes, suggests minimal fixes when a pair fails, and (optionally) writes
Color.kt + Theme.kt.

Unlike the old gen_tokens.py, this script does NOT invent a palette from
scratch. The user decides the colors; this script only ensures they don't
collide.

Usage:
  # One accent; neutrals are derived for display, NOT written without --write
  python3 validate_tokens.py "#3B5BA9"

  # Explicit palette (up to 6: accent, bg-light, bg-dark, text-light, text-dark, surface)
  python3 validate_tokens.py "#1A6B5A" --bg-light "#F7F9F8" --bg-dark "#0D1211" \
      --text-light "#1A2622" --text-dark "#E2E8E6"

  # Write Color.kt + Theme.kt
  python3 validate_tokens.py "#3B5BA9" --package com.myapp --out app/src/main/java/com/myapp/ui/theme --write

Without --write the result is printed to stdout for review.
"""
import argparse
import colorsys
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from contrast import parse as parse_color, ratio  # noqa: E402


def _rgb(hex_str):
    """Parse a hex color string and return just the (r, g, b) tuple."""
    _, rgb = parse_color(hex_str)
    return rgb


def to_hls(rgb):
    """Convert a (r, g, b) tuple of 0-255 ints to HLS floats in 0-1."""
    return colorsys.rgb_to_hls(*[x / 255 for x in rgb])


def from_hls(h, l, s):
    """Convert HLS (0-1) to a (r, g, b) tuple of 0-255 ints."""
    return tuple(round(x * 255) for x in colorsys.hls_to_rgb(h, min(max(l, 0), 1), min(max(s, 0), 1)))


def hex_s(rgb):
    return "#%02X%02X%02X" % rgb


def kt(rgb):
    return "0xFF%02X%02X%02X" % rgb


def neutral_from_accent(accent_rgb, lightness, sat=0.04):
    """Derive a neutral tinted slightly toward the accent hue."""
    h, _, _ = to_hls(accent_rgb)
    return from_hls(h, lightness, sat)


def build_schemes(accent_hex, explicit=None):
    """Build light/dark scheme dicts.

    accent_hex: str, the user's chosen accent color.
    explicit: optional dict with keys bg-light, bg-dark, text-light, text-dark, surface.
    """
    accent = _rgb(accent_hex)
    h, l, s = to_hls(accent)
    s = min(s, 0.6)
    explicit = explicit or {}

    # Neutrals: use explicit values if given, else derive (tinted 4% toward accent)
    bg_light = _rgb(explicit["bg-light"]) if "bg-light" in explicit else neutral_from_accent(accent, 0.965)
    bg_dark = _rgb(explicit["bg-dark"]) if "bg-dark" in explicit else neutral_from_accent(accent, 0.07)
    text_light = _rgb(explicit["text-light"]) if "text-light" in explicit else neutral_from_accent(accent, 0.11, 0.06)
    text_dark = _rgb(explicit["text-dark"]) if "text-dark" in explicit else neutral_from_accent(accent, 0.91, 0.04)

    surface_light = _rgb(explicit["surface"]) if "surface" in explicit else neutral_from_accent(accent, 0.995, 0.02)
    dl = to_hls(bg_dark)[1]  # keep dark surfaces stepping up from the real dark background
    surface_dark = neutral_from_accent(accent, dl + 0.03)
    sv_light = neutral_from_accent(accent, 0.93)
    sv_dark = neutral_from_accent(accent, dl + 0.07)
    ov_light = neutral_from_accent(accent, 0.85)
    ov_dark = neutral_from_accent(accent, dl + 0.17)
    osv_light = neutral_from_accent(accent, 0.36, 0.05)
    osv_dark = neutral_from_accent(accent, 0.67, 0.04)

    # Primary: adjust lightness until contrast passes
    p_light = list(accent)
    pl = l
    while ratio(p_light, bg_light) < 4.5 and pl > 0.05:
        pl -= 0.02
        p_light = list(from_hls(h, pl, s))

    p_dark = list(accent)
    pd = max(l, 0.70)
    while ratio(p_dark, bg_dark) < 4.5 and pd < 0.95:
        pd += 0.02
        p_dark = list(from_hls(h, pd, min(s, 0.65)))

    ink = (0x10, 0x14, 0x18)
    white = (255, 255, 255)

    def on(c):
        c = tuple(c)
        return white if ratio(white, c) >= ratio(ink, c) else ink

    light = {
        "primary": tuple(p_light), "onPrimary": on(p_light),
        "background": bg_light, "surface": surface_light,
        "surfaceVariant": sv_light, "outlineVariant": ov_light,
        "onSurface": text_light, "onSurfaceVariant": osv_light,
        "error": (0xB3, 0x26, 0x1E), "onError": white,
    }
    dark = {
        "primary": tuple(p_dark), "onPrimary": on(p_dark),
        "background": bg_dark, "surface": surface_dark,
        "surfaceVariant": sv_dark, "outlineVariant": ov_dark,
        "onSurface": text_dark, "onSurfaceVariant": osv_dark,
        "error": (0xF2, 0xB8, 0xB5), "onError": (0x60, 0x14, 0x10),
    }
    return light, dark


def suggest_fix(name, fg_c, bg_c, need):
    """Step the foreground lightness away from the background until the ratio passes."""
    h, l, s = to_hls(fg_c)
    step = 0.01 if to_hls(bg_c)[1] < 0.5 else -0.01  # lighten on dark bg, darken on light bg
    for _ in range(100):
        l += step
        cand = from_hls(h, l, s)
        if ratio(cand, bg_c) >= need:
            return f"change {name} from {hex_s(fg_c)} to about {hex_s(cand)}"
        if l <= 0 or l >= 1:
            break
    return f"{name} {hex_s(fg_c)} cannot reach {need}:1 on this background; change the background too"


def check_contrast(light, dark):
    """Return (rows, all_ok). Each row: (scheme, fg, bg, ratio, needed, ok, suggestion)."""
    pairs = [
        ("onSurface", "background", 4.5),
        ("onSurface", "surface", 4.5),
        ("onSurfaceVariant", "background", 4.5),
        ("onSurfaceVariant", "surface", 4.5),
        ("onPrimary", "primary", 4.5),
        ("primary", "background", 3.0),
        ("primary", "surface", 3.0),
        ("error", "background", 3.0),
        ("onError", "error", 4.5),
    ]
    rows = []
    all_ok = True
    for name, scheme in (("light", light), ("dark", dark)):
        for fg, bg, need in pairs:
            fg_c = tuple(scheme[fg])
            bg_c = tuple(scheme[bg])
            r = ratio(fg_c, bg_c)
            ok = r >= need
            if not ok:
                all_ok = False
            suggestion = suggest_fix(fg, fg_c, bg_c, need) if r < need else ""
            rows.append((name, fg, bg, r, need, ok, suggestion))
    return rows, all_ok


def print_report(rows, all_ok, light, dark):
    print("\n=== Contrast Verification ===")
    print(f"{'Scheme':<7} {'Foreground':<18} {'Background':<14} {'Ratio':>7}  {'Need':>5}  Status")
    print("-" * 72)
    for name, fg, bg, r, need, ok, suggestion in rows:
        status = "ok" if ok else f"FAIL -> {suggestion}"
        print(f"{name:<7} {fg:<18} {bg:<14} {r:5.2f}:1 {need:5.1f}  {status}")
    print()
    if not all_ok:
        print("Some pairs fail. Adjust the colors above and re-run.")
        print('Example: python3 validate_tokens.py "#3B5BA9" --bg-dark "#111111" --text-dark "#E0E0E0"')
    else:
        print("All pairs pass WCAG thresholds.")


def color_kt(pkg, light, dark):
    out = [f"package {pkg}.ui.theme", "", "import androidx.compose.ui.graphics.Color", ""]
    for prefix, sch in (("Light", light), ("Dark", dark)):
        for k, v in sch.items():
            out.append(f"internal val {prefix}{k[0].upper() + k[1:]} = Color({kt(v)})")
        out.append("")
    return "\n".join(out)


def scheme_kt(prefix, fn):
    names = ["primary", "onPrimary", "background", "surface", "surfaceVariant",
             "outlineVariant", "onSurface", "onSurfaceVariant", "error", "onError"]
    lines = [f"private val {prefix}Colors = {fn}("]
    for n in names:
        lines.append(f"    {n} = {prefix}{n[0].upper() + n[1:]}," )
    lines.append(f"    onBackground = {prefix}OnSurface,")
    lines.append(f"    outline = {prefix}OutlineVariant,")
    lines.append(")")
    return "\n".join(lines)


def theme_kt(pkg):
    return f"""package {pkg}.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable

{scheme_kt("Light", "lightColorScheme")}

{scheme_kt("Dark", "darkColorScheme")}

@Composable
fun AppTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit,
) {{
    MaterialTheme(
        colorScheme = if (darkTheme) DarkColors else LightColors,
        content = content,
    )
}}
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("accent", help="Primary/accent color hex (e.g. #3B5BA9)")
    ap.add_argument("--bg-light", help="Background for light scheme (default: derived)")
    ap.add_argument("--bg-dark", help="Background for dark scheme (default: derived)")
    ap.add_argument("--text-light", help="On-surface text for light scheme (default: derived)")
    ap.add_argument("--text-dark", help="On-surface text for dark scheme (default: derived)")
    ap.add_argument("--surface", help="Surface color for light scheme (default: derived)")
    ap.add_argument("--package", default="com.example.app", help="Kotlin package for output")
    ap.add_argument("--out", help="Output directory for Color.kt / Theme.kt")
    ap.add_argument("--write", action="store_true", help="Write files to --out (default: print only)")
    ap.add_argument("--force", action="store_true", help="Overwrite an existing Color.kt / Theme.kt")
    a = ap.parse_args()
    if a.write and not a.out:
        ap.error("--write needs --out <dir>")
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass

    explicit = {}
    if a.bg_light: explicit["bg-light"] = a.bg_light
    if a.bg_dark: explicit["bg-dark"] = a.bg_dark
    if a.text_light: explicit["text-light"] = a.text_light
    if a.text_dark: explicit["text-dark"] = a.text_dark
    if a.surface: explicit["surface"] = a.surface

    light, dark = build_schemes(a.accent, explicit or None)
    rows, all_ok = check_contrast(light, dark)
    print_report(rows, all_ok, light, dark)

    # Show the generated colors for review
    print("\n=== Generated Color Tokens ===")
    print("Light scheme:")
    for k, v in light.items():
        print(f"  Light{k[0].upper() + k[1:]:<24} {hex_s(tuple(v))}  ({kt(tuple(v))})")
    print("Dark scheme:")
    for k, v in dark.items():
        print(f"  Dark{k[0].upper() + k[1:]:<25} {hex_s(tuple(v))}  ({kt(tuple(v))})")

    # Write files only if requested AND all checks pass
    if a.write and a.out:
        if not all_ok:
            print("\n[skipped] Not writing files: contrast checks failed.", file=sys.stderr)
            sys.exit(1)
        existing = [n for n in ("Color.kt", "Theme.kt") if os.path.exists(os.path.join(a.out, n))]
        if existing and not a.force:
            print(f"\n[skipped] {', '.join(existing)} already exist in {a.out}. Merge by hand "
                  "(do not create a second design system) or pass --force.", file=sys.stderr)
            sys.exit(1)
        os.makedirs(a.out, exist_ok=True)
        with open(os.path.join(a.out, "Color.kt"), "w", encoding="utf-8", newline="\n") as f:
            f.write(color_kt(a.package, light, dark))
        with open(os.path.join(a.out, "Theme.kt"), "w", encoding="utf-8", newline="\n") as f:
            f.write(theme_kt(a.package))
        print(f"\nWritten: {a.out}/Color.kt, {a.out}/Theme.kt")
    elif not a.write:
        print(f"\n[review] Colors printed above. To write files:")
        print(f'  python3 validate_tokens.py {a.accent} --package {a.package} --out <dir> --write')
        print("  (only writes if all contrast checks pass)")

    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
