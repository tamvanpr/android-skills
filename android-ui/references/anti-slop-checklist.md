# Anti-slop checklist

Run this before reporting done. Answer yes or no. Every "no" in the Required section must be fixed.

## Required

- [ ] No emoji in code, strings, comments, or file names
- [ ] No decorative unicode characters used as icons
- [ ] One accent color, the rest neutral
- [ ] No decorative gradients
- [ ] No `Color(0x...)` outside the theme files
- [ ] Spacing only from the 4dp scale
- [ ] Typography only from `MaterialTheme.typography`
- [ ] Text contrast at least 4.5:1, components 3:1
- [ ] Both light and dark checked
- [ ] Touch targets at least 48dp
- [ ] Data screens have empty, loading, and error states
- [ ] `contentDescription` correct (meaningful or null)
- [ ] UI text lives in `strings.xml`, not hardcoded
- [ ] No new dependencies without approval
- [ ] Business logic untouched
- [ ] Dark mode elevation uses tonal shift (lighter surface = higher), not stacked shadows
- [ ] No entry/splash animation on every element; only important state transitions animate
- [ ] Focus order and tab navigation follow visual hierarchy; no focus traps
- [ ] No stock photos or AI-generated illustrations as placeholders; use vector icons + one sentence
- [ ] If 80% of existing screens already use token X, screen N+1 uses X too — do not introduce a new token for consistency's sake

## AI template tells (remove or replace)

| Symptom | Fix |
|---|---|
| Purple-blue gradient header | Solid neutral color |
| Every item wrapped in a shadowed card | Plain row + divider |
| Colored circle icons on every row | Remove, or keep one functional icon |
| Promotional headline ("Discover the new experience") | Functional headline ("Notes") |
| Long greeting text on the main page | Remove |
| Empty state with big illustration and emoji | One sentence + one action |
| Every button in the primary color | One primary, the rest outlined or text |
| Chips and badges with no purpose | Remove |
| 24dp+ radius on everything | 8/12/16 scale |
| Soft shadows on every surface | Tonal or thin line |
| Center alignment for long text | Left alignment |
| Dummy data that looks real ("John Smith, 3 hours ago") | Neutral, clearly marked placeholder |
| Entry animation on every element | Only important state transitions |
| Bold text everywhere | One emphasis level |
| Random color per category | One accent, differentiate via labels |

## Quick tests

1. **Blur test:** shrink or blur the screenshot. Does one main thing still stand out?
2. **Grayscale test:** is the hierarchy still readable?
3. **Removal test:** remove one element. Does anything lose its function? If not, leave it removed.
4. **Large font test:** at 1.5x, nothing clipped or overlapping?
5. **Narrow screen test:** at 360dp, no horizontal scrolling?
6. **Long content test:** text twice as long, does the layout hold?

## UI copy

- Short, clear, verbs for actions ("Save", "Delete").
- One language per app, unless it is truly multilingual via resources.
- No excessive exclamation marks, no promotional tone.
- Error messages name the cause and the next step.
- Empty states: one sentence + one action. No illustration, no emoji, no marketing copy.

## Consistency guard

- Before adding a new color, spacing value, or component style, check whether an existing token already covers it. If yes, reuse it.
- A new design decision on one screen must propagate to the others in the same module within the same PR.
- Do not mix two different visual languages in one module (e.g. card-based on screen A, flat list on screen B for the same content type).

## Honest reporting

If a checklist item cannot be met (e.g. a preview cannot run in this environment), say so plainly. Do not write "verified" for something that was not run.
