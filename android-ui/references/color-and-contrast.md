# Color and contrast

Goal: the UI looks calm and clear without looking "lacking" (washed out, flat, boundary-less). The trick is not more colors, but enough neutral depth plus one consistent accent.

## Palette structure

A screen only needs these roles:

| Role | Function | Material 3 |
|---|---|---|
| Background | Screen base | `background` |
| Surface | Content areas, bars | `surface` |
| Surface variant (tonal) | Subtle separation, fields, chips | `surfaceVariant`, `surfaceContainer*` |
| Outline | Thin lines | `outlineVariant` |
| Text primary | Headings, body | `onSurface` |
| Text secondary | Descriptions | `onSurfaceVariant` |
| Accent | Primary actions, active state | `primary` / `onPrimary` |
| Error | Errors | `error` |

If all roles above are filled, the UI rarely looks lacking. The problem usually appears when only two levels exist (white and light gray), so there is no hierarchy.

## Rules so it does not look lacking

1. **At least 3 neutral depth levels** per theme: background, surface, and a higher surface or variant. Luminance difference between levels around 3–6 percent.
2. **Use the accent sparingly but consistently**: primary buttons, selected state, focus indicators, links. Do not use it as a large-area background.
3. **Secondary text stays readable.** Never lower text opacity below 4.5:1. Avoid `alpha = 0.38` for text that must be read.
4. **Separators exist**, but are subtle: space first, then tonal shift, then a 1dp `outlineVariant` line.
5. **Status colors** (error, success, warning) may sit outside the single accent, but always paired with text or an icon, not color alone.
6. **Dark mode is designed**, not inverted. Dark: background around `#0F1114` to `#141619`, surfaces stepping up. The accent is softened (lower chroma, lighter) so it does not vibrate.
7. **Grayscale test.** Convert the screenshot to black and white. The hierarchy must still read.

## Choosing an accent

- If the user has a brand color, use it. Derive its tonal steps, do not change the hue.
- If not, pick one hue with medium chroma. Avoid neon purple-blue and gradients. Safe picks: steel blue, dark teal green, terracotta, olive green, dark indigo.
- Do not use more than one accent hue. If categories need differentiation, differentiate with shape, labels, or icons.
- Validate your chosen colors: `python3 scripts/validate_tokens.py "#3B5BA9" [--bg-dark "#0D1211"]`. The script prints all derived neutrals for both light and dark schemes, checks contrast, and only writes `Color.kt` / `Theme.kt` when you pass `--write` AND all checks pass.

## Example palettes (neutral, ready to use)

Light:

| Token | Hex |
|---|---|
| background | `#F7F7F5` |
| surface | `#FFFFFF` |
| surfaceVariant | `#EFEFEC` |
| outlineVariant | `#DADAD5` |
| onSurface | `#1B1C1A` |
| onSurfaceVariant | `#5B5D58` |
| primary | `#3B5BA9` |
| onPrimary | `#FFFFFF` |
| error | `#B3261E` |

Dark:

| Token | Hex |
|---|---|
| background | `#121312` |
| surface | `#1A1B1A` |
| surfaceVariant | `#252624` |
| outlineVariant | `#3A3B38` |
| onSurface | `#E6E6E2` |
| onSurfaceVariant | `#A9AAA4` |
| primary | `#9DB4F0` |
| onPrimary | `#14224A` |
| error | `#F2B8B5` |

Verify before using: `python3 scripts/contrast.py "#5B5D58" "#F7F7F5"`.

## Contrast (WCAG 2.2)

- Normal text: at least 4.5:1.
- Large text (18sp or 14sp bold) and UI components (field borders, action icons): at least 3:1.
- Disabled state may be lower, but never use it for important information.
- Text over images: use a solid scrim, do not rely on the image.

## Compose implementation

```kotlin
private val LightColors = lightColorScheme(
    primary = Color(0xFF3B5BA9),
    onPrimary = Color(0xFFFFFFFF),
    background = Color(0xFFF7F7F5),
    surface = Color(0xFFFFFFFF),
    surfaceVariant = Color(0xFFEFEFEC),
    outlineVariant = Color(0xFFDADAD5),
    onSurface = Color(0xFF1B1C1A),
    onSurfaceVariant = Color(0xFF5B5D58),
    error = Color(0xFFB3261E),
)
```

Hex values may only appear in this theme file. In screens, use `MaterialTheme.colorScheme.primary` and so on.

Dynamic color (Material You): do not enable by default when the user has a brand color. Make it an option and ask.

## Anti-patterns

- Pure white `#FFFFFF` as the main background everywhere, plus pure black text.
- Pure black `#000000` + pure white text (halos, tiring), except OLED-first.
- Gray via opacity over other colors (unpredictable results). Use solid colors from tokens.
- Random color per component for "variety".
- Accent gradients on buttons, headers, and backgrounds.
