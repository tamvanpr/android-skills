---
name: android-ui
description: >
  Build, rework, or audit the UI layer of native Android apps (Kotlin, Jetpack Compose, or XML Views).
  UI mode: minimalist, accessible, design tokens, screenshots.
  Security mode: WebView, exported components, deep links, intents, data leaks.
  Security mode is read-only unless asked to fix.
license: MIT
compatibility: opencode, Claude Code, Cursor, Windsurf, Codex, Gemini, Copilot
metadata:
  platform: android
  language: kotlin
  version: "2.3.0"
---

# Android UI (Build & Audit)

One skill for two jobs in the UI layer of native Android apps (Kotlin, Jetpack Compose, or XML Views):

- **UI mode** — building, reconstructing, or tidying up UI: minimalist, mature, accessible, consistent.
- **Security mode** — auditing the UI/frontend security layer: WebView, exported components, deep links, intents, on-screen data leaks, input validation, storage, secrets.

> **Scope limits.** This skill does not replace a full penetration test, backend security review, or human design critique. Security mode finds gaps in the frontend/UI layer only. Always verify AI output against official Android documentation for your specific AndroidX versions. If a rule here conflicts with an explicit user request, follow the user and state the consequence in one sentence.

---

## When to use

Pick the mode from the user's request:

| Mode | Triggers (examples) |
|---|---|
| **UI** | "Redesign this settings screen", "Make this screen look like the screenshot", "Fix the spacing on the profile page", "Theme my app dark", "Audit the visual consistency of these 3 screens" |
| **Security** | "Audit the security of the login screen", "Check for exported components", "Is my WebView safe?", "Pre-release security scan", "Find hardcoded secrets" |
| **Mixed** | "Tidy up this screen and make sure it's secure", "Redesign and harden the profile page" → run UI mode first, then Security mode over the same scope |

If the request is ambiguous, ask one clarifying question: *"Is this about how it looks and works, or about how safe it is (or both)?"*

---

## What to read (load only what the task needs)

References are not loaded automatically. Read only the rows that match the task:

| Task | Read first |
|---|---|
| New screen or rebuild from a screenshot | `references/clarifying-questions.md`, `references/reconstruction-workflow.md`, `references/compose-patterns.md` |
| Colors, theme, dark mode | `references/color-and-contrast.md` |
| Spacing, type, radius, forms, lists | `references/typography-spacing.md` |
| Final UI self-review | `references/anti-slop-checklist.md` |
| WebView or `AndroidView` | `references/webview.md`, `references/compose-risks.md` |
| Manifest, deep links, intents, FileProvider | `references/components-intents.md` |
| Login, PIN, payment, personal data screens | `references/sensitive-data-ui.md`, `references/compose-risks.md` |
| Input handling, navigation arguments | `references/input-and-state.md` |
| Network config, storage, secrets, release build | `references/network-storage.md` |
| Writing the audit report | `references/checklist.md`, `references/report-template.md` |

Scripts: use `python3` (on Windows use `py` or `python`). Quote hex colors in the shell: `"#3B5BA9"`.

---

## UI mode — Workflow (follow in order)

1. **Clarify first.** Read `references/clarifying-questions.md`. If any of the "ambiguous" conditions are met, stop and ask. At most 4 questions, multiple choice where possible, and include the default you recommend.
2. **Audit the current state.** Find the existing theme, tokens, and components (`Theme.kt`, `Color.kt`, `Type.kt`, `themes.xml`, `colors.xml`). Use what is there. Do not create a second design system.
3. **Define tokens before screens.** Ask the user for their color choices (accent, backgrounds, text colors). Then validate with `python3 scripts/validate_tokens.py <accent> [--bg-light ...] [--bg-dark ...] [--text-light ...] [--text-dark ...]` to confirm contrast passes in both schemes. Only write `Color.kt` / `Theme.kt` after the user confirms the printed values. See `references/color-and-contrast.md` and `references/typography-spacing.md`.
4. **Build the screens** using the patterns in `references/compose-patterns.md` (or the XML equivalents if the project uses Views).
5. **Run the automated checks:**
   - `python3 scripts/lint_ui.py <project-path>` to catch style violations.
   - `python3 scripts/contrast.py <fg> <bg>` to verify individual color pairs.
   - `python3 scripts/validate_tokens.py <accent> ...` to validate the full token set (light + dark).
6. **Self-review** with `references/anti-slop-checklist.md`. Fix issues before reporting done.
7. **Verify compilation, then report** (see the Safety rules below).

## UI mode — Hard rules

**Emoji and decorative symbols**
- No emoji in UI, string resources, file names, comments, or commit messages unless the user explicitly asks.
- No stand-in icon characters (e.g. asterisks, unicode arrows, unicode checkmarks). Use Material `Icons` or vector drawables.
- Do not add icons just to fill space. An icon must carry meaning or an action.

**Ask, don't guess**
- If the platform (Compose or Views), the screen's purpose, the real data, or the visual direction is unclear, ask.
- If the user attaches a screenshot, treat it as the structural reference. Ask whether the colors and fonts must be kept or may be changed.
- Do not invent features, marketing copy, or dummy data that looks real. Use neutral placeholders and mark them clearly.

**Color**
- One accent color. Everything else neutral. At most two color families per screen, excluding status colors (error, success).
- All colors go through theme tokens (`MaterialTheme.colorScheme.*` or theme attributes). `Color(0xFF...)` inside screen composables is forbidden.
- Body text needs at least 4.5:1 contrast; large text and functional icons at least 3:1. Verify with `scripts/contrast.py`.
- Provide both a light and a dark scheme. Dark is not pure black `#000000` unless the user asks for an OLED-first screen. Light is not blinding white forced onto every surface.
- No decorative gradients, glows, or stacked shadows unless asked.

**Layout**
- 4dp spacing grid. Preferred values: 4, 8, 12, 16, 24, 32, 48 (the linter only rejects non-multiples of 4). No ad-hoc numbers like 13dp or 27dp.
- One clear hierarchy per screen: one heading, one primary action.
- Separate with space and tonal surfaces first, then a thin divider, and cards only when an element truly stands alone. Do not wrap everything in cards.
- Touch targets at least 48dp. Content must not be clipped at font scale 1.3 and a 360dp screen.
- Support edge-to-edge and window insets properly.

**Typography**
- At most two weights per screen. Use the `MaterialTheme.typography` scale. No ad-hoc `fontSize = 17.sp`.
- Text in `sp`, distances in `dp`.

**Motion**
- Only motion that explains a state change. Durations 150–250 ms. Respect the "remove animations" setting.

**Accessibility**
- `contentDescription` meaningful for action icons, `null` for decorative ones.
- Do not rely on color alone to communicate state.

**Scope of changes**
- Change only what was asked. No refactoring the architecture, swapping libraries, or moving packages unless asked.
- Do not add new dependencies without asking.
- Do not touch business logic when reconstructing the UI. Separate state and events from the view (state hoisting).

## UI mode — "AI slop" signs to avoid

Purple-to-blue gradients, very large corner-radius cards with shadows everywhere, colored circle icons on every row, marketing-style headlines ("Welcome to the new experience"), empty states with emoji illustrations, badges and chips with no purpose, every button in the primary color, uniform spacing with no rhythm. The full list is in `references/anti-slop-checklist.md`.

---

## Safety rules (MANDATORY, all modes)

Goal: no commit that breaks the build, no red CI, and no feature "reversed" back to an old version just to get green.

- **Verify before pushing.** If the project has Gradle, run the relevant compile and unit tests (e.g. `./gradlew compileDebugKotlin` then `:app:testDebugUnitTest`) and fix until they pass BEFORE pushing. If they cannot run in the agent's environment (no JDK/SDK), say so explicitly and limit changes to small pieces that are certainly safe.
- **One commit = one complete, compilable thing.** Never send a dangling piece (a parameter without a definition, a missing import, a half-finished function). Split big changes into several sequential commits, each of which still builds.
- **Fix forward, don't back up.** The build is broken because of your change? Fix the change, not by undoing the design. Rollback is only allowed as the user's decision.
- **Keep project conventions.** Strings go through resources (`stringResource`), names and structure follow the project's existing patterns. Do not change working conventions unasked.
- **Report what was verified.** In the final report, name the checks that actually ran (compile, tests, linter, contrast) and the ones that could not run.

---

## Security mode — Workflow

1. **Define the scope.** Which folder, which module, which build variant (debug or release), which targetSdk. If unclear, ask. Do not inspect outside the folder given.
2. **Automated scan:**
   ```
   python3 scripts/scan.py <project-path> --format md --out security-report.md
   ```
   Options: `--min-severity medium`, `--format json`, `--fail-on high` (for CI), `--include-tests`.
3. **Manually verify every finding.** The scanner is regex, not data-flow analysis. Open the file, read the context, decide whether it is actually exploitable. Mark each finding as confirmed, possible, or false positive.
4. **Trace what the scanner does not catch** using `references/checklist.md`: deep link logic, login flows, payment screens, token storage, share intents, FileProvider.
5. **Report** with `references/report-template.md`. Order by severity; include location, impact, and a concrete fix.
6. **Fix only when asked** — and follow the Safety rules above (minimal change per finding, one finding one change, compilation passes, explain the side effects).

## Security mode — Hard rules

- **Read-only by default.** Do not modify files, add dependencies, or change build configuration unless the user asks for fixes.
- **Do not write exploits.** No malware, active payloads, or ready-to-use PoCs against other people's apps. Explain reproduction steps conceptually and minimally (e.g. "send an intent with extra X to activity Y") for the user's own app.
- **Only the user's own app, or one explicitly authorized.** If it looks like the user is asking to attack a third-party app, stop and state the limit.
- **Do not print full secrets.** If you find an API key, token, or private key, show only the first 4 characters and recommend rotation.
- **Do not claim "safe".** Say "no issues found in this pass" and name what was not checked.
- **Ask when ambiguous.** Unclear whether this is a public or internal app, whether it processes sensitive data, or what the release target is. That context changes the severity.
- **Distinguish debug from release.** Findings in `src/debug/` or behind `BuildConfig.DEBUG` are downgraded, but still recorded if they can leak into release.
- **Be honest about limits.** This scanner does not replace a pentest, an architecture review, or backend analysis.
- **No emoji** in reports or code.

## Security mode — Severity levels

| Level | Meaning | Examples |
|---|---|---|
| critical | Directly exploitable, high impact | Trust-all SSL, private key in the repo |
| high | Exploitable under mild conditions | `addJavascriptInterface` with untrusted content, exported provider without a permission |
| medium | Needs specific conditions or weakens a defense | No FLAG_SECURE on a sensitive screen, `allowBackup` enabled |
| low | Hardening | Logging stack traces, `printStackTrace()` |
| info | Point to check manually | Deep link parameter |

Assessment details are in `references/report-template.md`.

## Security mode — Coverage

1. WebView and web content (`references/webview.md`)
2. Components, intents, deep links, PendingIntent, FileProvider (`references/components-intents.md`)
3. Sensitive data on screen: screenshots, recents, clipboard, autofill, keyboard, logs, persisted state (`references/sensitive-data-ui.md`)
4. Inputs and state: injection, path traversal, untrusted navigation arguments (`references/input-and-state.md`)
5. Network and storage from the UI perspective (`references/network-storage.md`)
6. Compose-specific: `rememberSaveable`, semantics, `AndroidView`, text fields (`references/compose-risks.md`)

## Security mode — Suppressing false positives

Add a comment on the same line or the line above. The reason is required: the scanner ignores a `sec-ignore` that has no reason.

```kotlin
// sec-ignore: W-JS local content from assets, no external URLs loaded
settings.javaScriptEnabled = true
```

In `AndroidManifest.xml`, put `<!-- sec-ignore: M-EXPORT reason -->` directly above the element.
Do not suppress a finding without a written reason.

---

## Handling script output

When running the automated scripts, follow these rules:

- **`lint_ui.py` reports violations.** Fix each violation before proceeding to the next workflow step. If a violation is intentional (e.g. a design decision), add `// ui-ignore: RULE_ID reason` on the offending line (or the line above; `lint-override:` works as an alias) and note it in the report.
- **`contrast.py` fails (ratio below threshold).** Adjust the color tokens (lighten/darken the foreground or background) and re-run until every pair passes. Do not lower the threshold to make it pass.
- **`validate_tokens.py` reports a failing pair.** It prints a suggested lightness adjustment. Apply the suggestion (or pick your own value), re-run, and repeat until all pairs pass. The script only writes files when `--write` is passed AND all checks pass; without `--write` it prints the tokens for user review.
- **`scan.py` exits 2 or prints "Nothing was scanned".** The path was wrong or held no source files. That is not a clean result; fix the path and rerun.
- **`scan.py` finds issues.** Classify each finding as **confirmed**, **possible**, or **false positive** before including it in the report. A confirmed finding means you opened the file, read the context, and verified exploitability. Possible means the pattern matches but context is unclear. False positive means the pattern matches but the code is safe (explain why in one line).
- **Any script exits non-zero (other than expected "violations found").** Report the error verbatim, do not guess the cause, and ask the user for context (e.g. Python version, missing module).

---

## File map

| File | Contents |
|---|---|
| `references/clarifying-questions.md` | When to ask, question templates |
| `references/color-and-contrast.md` | How to pick a palette, ready-made neutral palettes, contrast rules |
| `references/typography-spacing.md` | Type scale, spacing, radius, elevation |
| `references/compose-patterns.md` | Compose code patterns and XML equivalents |
| `references/reconstruction-workflow.md` | How to read a screenshot or an old screen and reconstruct it |
| `references/anti-slop-checklist.md` | Final checklist |
| `references/checklist.md` | Numbered security checklist (IDs are used by the scanner and the report) |
| `references/webview.md` | Safe WebView configuration and anti-patterns |
| `references/components-intents.md` | Exported, intent filters, deep links, PendingIntent |
| `references/sensitive-data-ui.md` | Leaks through the screen and device |
| `references/input-and-state.md` | Input validation and external data |
| `references/network-storage.md` | Cleartext, trust managers, storage |
| `references/compose-risks.md` | Compose-specific risks |
| `references/report-template.md` | Report format and severity assessment |
| `scripts/lint_ui.py` | Style linter for `.kt` and `.xml` |
| `scripts/contrast.py` | WCAG contrast calculator |
| `scripts/validate_tokens.py` | Validates a user-chosen color set (light + dark contrast); optionally writes `Color.kt` / `Theme.kt` |
| `scripts/scan.py` | Static security scanner |

## Finding the scripts

The `scripts/...` paths above are relative to this skill folder, not the project folder. Use the base directory provided when the skill is loaded. If there is none, search:

```
find ~/.config/opencode .opencode ~/.claude .claude -path '*android-ui/scripts/scan.py' 2>/dev/null
```

---

## Verification checklist

Before reporting any task as done, confirm:

- [ ] Design tokens (color, typography, spacing, radius) are defined in one place.
- [ ] No hardcoded `Color(0xFF...)` or ad-hoc `fontSize` in screen composables.
- [ ] All interactive elements have minimum 48dp touch targets.
- [ ] `lint_ui.py` passes (or violations are individually overridden with reason).
- [ ] `contrast.py` passes for every foreground/background pair in use.
- [ ] `scan.py` completed and all findings classified (confirmed / possible / false positive).
- [ ] Compilation verified (Gradle or equivalent) before pushing.
- [ ] Anti-slop checklist reviewed and no items violated.
