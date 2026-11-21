# UI reconstruction workflow

Used when the user provides a screenshot, an old screen, or a description and asks for a cleaner rebuild.

## 1. Inventory

Write down what is on the screen, without judging:
- Elements (headings, lists, fields, buttons, navigation)
- Data displayed
- Actions available
- Visible states (empty, loading, error, selected)

If from a screenshot, name what cannot be confirmed (font, original sizes, exact colors) and ask if it matters.

## 2. Set the hierarchy

Answer three things:
1. What is this screen's one primary purpose?
2. What is the one primary action?
3. What can be dropped or moved to another screen?

Elements that do not answer those three questions are candidates for removal or demotion.

## 3. Map to tokens

Replace every ad-hoc value with a token:
- Color: pick the closest role (`surface`, `onSurfaceVariant`, `primary`).
- Spacing: round to the 4dp scale.
- Typography: pick the closest style from the scale.
- Radius: pick from the three levels.

Note mappings that change the appearance meaningfully, for the report.

## 4. Simplify

Pruning order:
1. Remove decoration without function (gradients, stacked shadows, ornamental icons).
2. Merge nested containers (card inside card).
3. Align everything to one left edge.
4. Reduce the number of text styles.
5. Reduce colors to one accent + neutrals.

## 5. Build

Follow `compose-patterns.md`. Start from state and events, then composition, then previews.

## 6. Verify

- Previews: light, dark, font scale 1.5, width 360dp.
- `python3 scripts/lint_ui.py <path>`.
- Contrast of the main color pairs.
- The checklist in `anti-slop-checklist.md`.

## 7. Report

Short format:

```
Done: <screen>
Decisions: <accent, list structure, etc.>
Changed: <files>
Deliberately not done: <things left unchanged and why>
Needs confirmation: <if any>
```

## Preserving behavior

Reconstruction must not change behavior. Preserve:
- Public function names and signatures called from outside the screen
- Navigation and route arguments
- Test IDs (`testTag`, `android:id`) already in use
- Text referenced by tests or localization (change via `strings.xml`, never hardcode)

If you must change any of them, state it explicitly in the report.
