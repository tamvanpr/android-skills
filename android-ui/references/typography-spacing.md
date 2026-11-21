# Typography, spacing, radius, elevation

## Spacing (multiples of 4dp)

| Token | Value | Use |
|---|---|---|
| `xs` | 4dp | Icon-to-label gap, tight line-to-line text |
| `sm` | 8dp | Gap inside a component |
| `md` | 12dp | Vertical padding of list rows |
| `lg` | 16dp | Screen margins, gap between small groups |
| `xl` | 24dp | Gap between sections |
| `xxl` | 32dp | Big section gaps, top space under a header |
| `touch` | 48dp | Minimum touch-target height |

Screen horizontal margins: 16dp on phones, 24dp on small tablets. Consistent across the app.

```kotlin
object Space {
    val xs = 4.dp; val sm = 8.dp; val md = 12.dp
    val lg = 16.dp; val xl = 24.dp; val xxl = 32.dp
}
```

Rhythm rule: space inside a group is smaller than space between groups. If every gap is equal, the hierarchy is lost.

## Typography

Use the Material 3 scale through `MaterialTheme.typography`. Do not invent new sizes in screens.

| Role | Style | Notes |
|---|---|---|
| Screen title | `titleLarge` | One per screen |
| Section heading | `titleMedium` | Medium weight |
| Body | `bodyLarge` / `bodyMedium` | Regular weight |
| Description | `bodySmall` | `onSurfaceVariant` |
| Button | `labelLarge` | |

Rules:
- At most two weights per screen (regular and medium, or regular and semibold).
- No all-caps for long text. Short titles only, and avoid aggressive `letterSpacing`.
- Comfortable line length is 40–75 characters. On tablets, cap content width (`widthIn(max = 640.dp)`).
- Line height 1.4–1.6 for body.
- Font: the system default is good. At most one custom font family, loaded via a font resource, not from an unverified URL.
- Tabular figures (`fontFeatureSettings = "tnum"`) for numeric columns so they align.

## Radius

Pick one scale and use it consistently:

| Token | Value | Use |
|---|---|---|
| `small` | 8dp | Chips, fields |
| `medium` | 12dp | Cards, small dialogs |
| `large` | 16dp | Bottom sheets |

Do not use a uniform large radius (24dp+) on every element. It reads quickly as a template.

## Elevation and boundaries

Preference order for separating elements:
1. Space
2. Tonal difference (`surfaceContainer`)
3. A 1dp `outlineVariant` line
4. Shadow (only for elements that truly float: FAB, menus, dialogs)

No stacked shadows, no glows, no thick colored borders.

## Icons

- One set (Material Symbols or `Icons.Outlined`). Do not mix filled and outlined styles at random.
- 24dp standard, 20dp for inline with text.
- Unlabeled icons only for very common actions (back, close, search).

## Lists

- Plain rows with a thin divider or space are enough for homogeneous lists.
- Cards only when each item has several parts and its own action.
- A leading visual (avatar, icon) only when it identifies the item. Not decoration.
- Use a stable `key` in `LazyColumn`.

## Forms

- Labels always visible (not just a placeholder).
- Error messages below the field, clear, with text.
- One primary button. Secondary actions as text buttons.
- Set `KeyboardOptions` to match the content (email, number, password) and `imeAction`.

## Empty, loading, error

All three states are required for every data screen:
- Empty: one explanatory sentence + one action if relevant. No decorative illustration.
- Loading: a simple indicator or a neutral skeleton. Do not block the whole screen if partial data exists.
- Error: what failed and what can be done (retry).
