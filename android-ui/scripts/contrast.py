#!/usr/bin/env python3
"""WCAG 2.2 contrast calculator.

Usage:
  python3 contrast.py <fg> <bg> [<fg2> <bg2> ...]

Colors: #RGB, #RRGGBB, 0xFFRRGGBB, or AARRGGBB (Android order).
If fg has an alpha, it is blended over bg before the calculation.
Exit code 1 if any pair fails AA for normal text (4.5:1), 2 on bad input.
Quote colors in the shell: "#3B5BA9" (an unquoted # starts a comment in sh).
"""
import sys


def parse(s):
    h = s.strip().lstrip("#")
    if h.lower().startswith("0x"):
        h = h[2:]
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if len(h) == 6:
        h = "FF" + h
    if len(h) != 8:
        raise ValueError(f"unknown color format: {s}")
    a = int(h[0:2], 16) / 255
    return a, tuple(int(h[i:i + 2], 16) for i in (2, 4, 6))


def blend(fg, a, bg):
    return tuple(round(f * a + b * (1 - a)) for f, b in zip(fg, bg))


def lin(c):
    c /= 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def lum(rgb):
    r, g, b = map(lin, rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def ratio(fg, bg):
    hi, lo = sorted((lum(fg), lum(bg)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def main(argv):
    if len(argv) < 2 or len(argv) % 2:
        print(__doc__)
        return 2
    failed = False
    for i in range(0, len(argv), 2):
        try:
            a, fg = parse(argv[i])
            _, bg = parse(argv[i + 1])
        except ValueError as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
        eff = blend(fg, a, bg) if a < 1 else fg
        r = ratio(eff, bg)
        aa = r >= 4.5
        large = r >= 3.0
        aaa = r >= 7.0
        failed |= not aa
        print(f"{argv[i]:>12} on {argv[i + 1]:<12} {r:5.2f}:1  "
              f"normal text AA {'pass' if aa else 'FAIL'} | "
              f"large text/component {'pass' if large else 'FAIL'} | AAA {'pass' if aaa else 'no'}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
