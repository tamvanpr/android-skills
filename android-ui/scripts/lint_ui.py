#!/usr/bin/env python3
"""UI style linter for Android projects (Kotlin Compose and XML Views).

Checks violations of the android-ui skill rules (UI mode):
emoji, hardcoded colors, gradients, ad-hoc font sizes, spacing off the 4dp
scale, large radius, heavy shadows, empty contentDescription, hardcoded text.

Usage:
  python3 lint_ui.py <path> [--json] [--strict] [--include-tests]

Exit code: 1 if there are errors (or warns with --strict), else 0.
Suppress a rule on a line (or the line above) with a comment that states a reason:
  // ui-ignore: RULE_ID reason   (alias: lint-override)
"""
import argparse
import json
import os
import re
import sys

SKIP_DIRS = {"build", ".git", ".gradle", ".idea", ".cxx", "node_modules", "generated"}
THEME_FILES = {"Color.kt", "Theme.kt", "Type.kt", "Shape.kt", "Spacing.kt", "Dimens.kt",
               "colors.xml", "themes.xml", "styles.xml", "dimens.xml", "strings.xml", "attrs.xml"}

EMOJI = re.compile("[\U0001F000-\U0001FAFF\u2600-\u27BF\u2B50\u2B55\uFE0F]")
SYMBOL = re.compile("[\u2190-\u21FF\u2022]")
IGNORE = re.compile(r"(?:ui-ignore|lint-override):\s*([A-Z_]+)")

HEX_KT = re.compile(r"Color\(\s*0x[0-9A-Fa-f]{6,8}\s*\)|Color\.parseColor\(")
NAMED = re.compile(r"\bColor\.(Red|Green|Blue|Yellow|Cyan|Magenta|Gray|LightGray|DarkGray)\b")
PURE = re.compile(r"\bColor\.(Black|White)\b|0xFF000000|0xFFFFFFFF")
GRADIENT = re.compile(r"Brush\.(linear|vertical|horizontal|radial|sweep)Gradient|<gradient")
FONT_SIZE = re.compile(r"fontSize\s*=\s*\d+(\.\d+)?\.sp")
DP = re.compile(r"(\d+(?:\.\d+)?)\.dp")
DP_CTX = re.compile(r"padding|spacedBy|\.size\(|height|width|offset|Spacer|defaultMinSize")
RADIUS = re.compile(r"RoundedCornerShape\(\s*(\d+(?:\.\d+)?)\.dp")
ELEVATION = re.compile(r"[eE]levation\s*=\s*(\d+(?:\.\d+)?)\.dp|\.shadow\(")
CD_EMPTY = re.compile(r'contentDescription\s*=\s*""')
TEXT_LIT = re.compile(r'\bText\(\s*(text\s*=\s*)?"[^"$]*[A-Za-z][^"$]*"')
ALPHA_TEXT = re.compile(r"color\s*=.*\.copy\(\s*alpha\s*=\s*0\.[0-5]")
DURATION = re.compile(r"durationMillis\s*=\s*(\d+)")
CARD = re.compile(r"\b(Elevated|Outlined)?Card\(")
TOUCH = re.compile(r"IconButton\(|\.clickable|\.toggleable|\.selectable")
SIZE_DP = re.compile(r"\.(?:size|height|width|heightIn|widthIn)\(\s*(?:min\s*=\s*)?(\d+(?:\.\d+)?)\.dp")

X_HEX = re.compile(r"#[0-9A-Fa-f]{6,8}\b")
X_TEXTSIZE = re.compile(r'android:textSize="\d+(\.\d+)?(sp|dp)"')
X_TEXT = re.compile(r'android:text="(?!@)[^"]*[A-Za-z][^"]*"')
X_DP = re.compile(r'android:(layout_margin\w*|padding\w*)="(\d+(?:\.\d+)?)dp"')


def is_theme(path):
    p = path.replace("\\", "/").lower()
    return os.path.basename(path) in THEME_FILES or "/theme/" in p or "/ui/theme" in p


def off_scale(v):
    f = float(v)
    return f not in (0, 0.5, 1, 2) and f % 4 != 0


def lint_kotlin(path, lines, out):
    theme = is_theme(path)
    cards = 0
    for i, line in enumerate(lines, 1):
        s = line.strip()
        is_comment = s.startswith("//") or s.startswith("*") or s.startswith("/*")
        if not theme and not is_comment:
            if HEX_KT.search(line):
                out.append((path, i, "error", "HEX_COLOR", "Hardcoded color outside the theme. Use MaterialTheme.colorScheme."))
            if NAMED.search(line):
                out.append((path, i, "error", "NAMED_COLOR", "Named color (Color.Red etc.). Use theme tokens."))
            if PURE.search(line):
                out.append((path, i, "warn", "PURE_BW", "Pure black or white. Use theme tokens (onSurface, surface)."))
            if FONT_SIZE.search(line):
                out.append((path, i, "error", "FONT_SIZE", "Ad-hoc fontSize. Use MaterialTheme.typography."))
            if ALPHA_TEXT.search(line):
                out.append((path, i, "warn", "FADED_TEXT", "Text with low alpha; contrast may fall below 4.5:1."))
            no_radius = RADIUS.sub("", line)
            if DP_CTX.search(no_radius):
                for m in DP.finditer(no_radius):
                    if off_scale(m.group(1)):
                        out.append((path, i, "warn", "DP_OFF_SCALE",
                                    f"{m.group(1)}.dp is not a multiple of 4 (preferred: 4, 8, 12, 16, 24, 32, 48)."))
                        break
            for m in RADIUS.finditer(line):
                if float(m.group(1)) >= 24:
                    out.append((path, i, "warn", "RADIUS_LARGE", "Radius of 24dp or more. Use the 8/12/16 scale."))
            m = ELEVATION.search(line)
            if m and (m.group(0).startswith(".shadow") or float(m.group(1)) >= 8):
                out.append((path, i, "warn", "HEAVY_SHADOW", "Heavy shadow. Prefer tonal surfaces or a thin line."))
            if TOUCH.search(line):
                for m in SIZE_DP.finditer(line):
                    if 1 < float(m.group(1)) < 48:
                        out.append((path, i, "warn", "TOUCH_TARGET",
                                    f"Interactive element sized {m.group(1)}dp; touch targets need at least 48dp."))
                        break
            m = DURATION.search(line)
            if m and int(m.group(1)) > 400:
                out.append((path, i, "warn", "SLOW_ANIM", f"Animation of {m.group(1)} ms. Target 150-250 ms."))
        if not is_comment:
            if GRADIENT.search(line):
                out.append((path, i, "warn", "GRADIENT", "Gradient. Avoid unless asked."))
            if CD_EMPTY.search(line):
                out.append((path, i, "warn", "CD_EMPTY", 'contentDescription = "". Use null for decorative elements.'))
            if TEXT_LIT.search(line):
                out.append((path, i, "info", "HARDCODED_TEXT", "Hardcoded text. Move it to strings.xml."))
            if CARD.search(line):
                cards += 1
    if cards > 4:
        out.append((path, 1, "info", "CARD_HEAVY", f"{cards} Cards in one file. Consider plain rows."))


def lint_xml(path, lines, out):
    p = path.replace("\\", "/")
    ui_xml = "/res/layout" in p or "/res/drawable" in p
    for i, line in enumerate(lines, 1):
        if ui_xml:
            if "tools:" in line:
                continue
            if X_HEX.search(line):
                sev = "warn" if "/res/drawable" in p else "error"
                out.append((path, i, sev, "HEX_COLOR_XML", "Hardcoded color in a layout/drawable. Reference a theme attribute."))
            if X_TEXTSIZE.search(line):
                out.append((path, i, "warn", "FONT_SIZE_XML", "Hardcoded textSize. Use textAppearance."))
            if X_TEXT.search(line):
                out.append((path, i, "info", "HARDCODED_TEXT", "Hardcoded text. Move it to strings.xml."))
            for m in X_DP.finditer(line):
                if off_scale(m.group(2)):
                    out.append((path, i, "warn", "DP_OFF_SCALE", f"{m.group(2)}dp is off the 4dp scale."))
            if "<gradient" in line:
                out.append((path, i, "warn", "GRADIENT", "Gradient. Avoid unless asked."))


def walk(root, include_tests):
    if os.path.isfile(root):
        yield root
        return
    for d, dirs, files in os.walk(root):
        dirs[:] = [x for x in dirs if x not in SKIP_DIRS
                   and (include_tests or x not in ("test", "androidTest"))]
        for f in files:
            if f.endswith((".kt", ".xml", ".java")):
                yield os.path.join(d, f)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--strict", action="store_true", help="warns also fail (exit 1)")
    ap.add_argument("--include-tests", action="store_true")
    a = ap.parse_args()
    if not os.path.exists(a.path):
        print(f"error: path not found: {a.path}", file=sys.stderr)
        sys.exit(2)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass

    found = []
    for path in walk(a.path, a.include_tests):
        try:
            with open(path, encoding="utf-8", errors="replace") as fh:
                lines = fh.read().splitlines()
        except OSError:
            continue
        local = []
        for i, line in enumerate(lines, 1):
            if EMOJI.search(line):
                local.append((path, i, "error", "EMOJI", "Emoji or decorative symbol. Remove it."))
            elif SYMBOL.search(line):
                local.append((path, i, "warn", "SYMBOL", "Decorative unicode character (arrow, bullet). Use an icon or text."))
        if path.endswith((".kt", ".java")):
            lint_kotlin(path, lines, local)
        elif path.endswith(".xml"):
            lint_xml(path, lines, local)
        for f in local:
            ln = f[1]
            ctx = " ".join(lines[max(0, ln - 2):ln])
            m = IGNORE.search(ctx)
            if m and m.group(1) == f[3]:
                continue
            found.append(f)

    order = {"error": 0, "warn": 1, "info": 2}
    found.sort(key=lambda f: (order[f[2]], f[0], f[1]))
    counts = {k: sum(1 for f in found if f[2] == k) for k in order}

    if a.json:
        print(json.dumps({"counts": counts, "findings": [
            {"file": f[0], "line": f[1], "severity": f[2], "rule": f[3], "message": f[4]} for f in found]},
            indent=2, ensure_ascii=False))
    else:
        for f in found:
            print(f"[{f[2].upper():5}] {f[3]:15} {f[0]}:{f[1]}  {f[4]}")
        print(f"\nSummary: {counts['error']} error, {counts['warn']} warn, {counts['info']} info")

    bad = counts["error"] + (counts["warn"] if a.strict else 0)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
