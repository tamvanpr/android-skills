# Android Skills

One skill for Android work: `android-ui`, with two modes — **UI** (building, reconstructing, and polishing Android UIs) and **security** (auditing the Android UI/frontend layer). Works with OpenCode, Claude Code, Codex CLI, Gemini CLI, GitHub Copilot, Cursor, and Windsurf.



## Installation

### Via npm / npx

```bash
# straight from the repo (no clone); requires python3 on the machine
npx tamvanpr/android-skills --help
npx tamvanpr/android-skills --target claude --project .
npx tamvanpr/android-skills --target cursor
```

Or install globally. A global `npm i -g` also auto-installs the skill into the OpenCode global config (`~/.config/opencode`) as long as `python3` is on PATH. Local installs and `npx` runs never write outside their target (set `ANDROID_SKILLS_SKIP_POSTINSTALL=1` to disable the global hook as well):

```bash
npm i -g android-skills
```

If `python3` is missing, the npm install still succeeds and prints a hint; install Python, then run `android-skills` once. For other agents or per-project installs, pass arguments:

```bash
android-skills --target codex --project .
android-skills --uninstall --target opencode
```

`android-skills` is a wrapper that runs `install.py` with the same arguments; the installer still needs `python3` on PATH.

### Via git / ZIP

```bash
git clone https://github.com/tamvanpr/android-skills.git
cd android-skills
python3 install.py
```

Or from a ZIP: extract, enter the `android-skills` folder, then run `python3 install.py`.

Available flags: `--project DIR`, `--target`, `--link`, `--agents-md`, `--uninstall`, `--validate` (see `--help`).

## Supported agents

| Target | Mechanism | Global location | Project location |
|---|---|---|---|
| `opencode` | skill folder + commands | `~/.config/opencode/` | `<project>/.opencode/` |
| `claude` | skill folder | `~/.claude/skills/` | `<project>/.claude/skills/` |
| `codex` | `AGENTS.md` instructions + `<root>/.android-skills/` | `~/.codex/` | `<project>/` |
| `gemini` | `GEMINI.md` instructions + skill folder | `~/.gemini/` | `<project>/` |
| `copilot` | `.github/copilot-instructions.md` + skill folder | — (project only) | `<project>/.github/` |
| `cursor` | `.mdc` rules in `<root>/rules/` + skill folder | `~/.cursor/` | `<project>/.cursor/` |
| `windsurf` | `.md` rules in `<root>/rules/` + skill folder | `~/.windsurf/` | `<project>/.windsurf/` |

For `codex`, `gemini`, and `copilot`, the installer copies the skills into the skill folder and adds a managed instruction block (`<!-- android-skills:begin -->`) to the rules file. The block is removed automatically by `--uninstall`.

For `cursor` and `windsurf`, the installer writes one rules file per skill (with `alwaysApply: false`) plus copies the skill folder so references and scripts remain accessible. If the agent's UI does not pick up the global rules, add them through the rules panel.

OpenCode also reads `.claude/skills` and `~/.claude/skills`. Install into only one of the two locations, otherwise the same skill name is loaded twice (the installer prints a note when it detects this).

Reinstalling overwrites the old version. To update: `git pull` then run `install.py` again (not needed when using `--link`). For the npm route, rerun `npx tamvanpr/android-skills ...` or `npm i -g` again.

On Termux (Android), just install `python3` and `git` via `pkg install python git`. The global path stays `~/.config/opencode`.

After installing, restart the OpenCode session. If a skill does not show up, check the folder name, the capitalization of `SKILL.md`, and the `skill` permission on the agent being used.

## Using it in OpenCode

There are three ways:

1. **Automatic.** OpenCode shows the skill name and description to the agent, and the agent loads it via the `skill` tool when the request matches.
2. **`@` mention.** In OpenCode v2, type `@android-ui` in the prompt to load a skill manually. v1 does not have this feature; just ask "load the android-ui skill".
3. **Commands.** `/ui <screen|folder>` is an optional shortcut from the `opencode/commands` folder; the right mode is picked from the argument and context.

Examples:

```text
@android-ui
Rework the settings screen. Keep all existing functionality and state.
```

```text
@android-ui
Audit frontend security on app/src/main, debug and release variants.
Do not modify files; report findings and false positives.
```

The skill ID follows the folder name (`android-ui`). Do not rename the `android-ui` folder.

References and scripts are not loaded automatically. The skills instruct the agent to read relevant references and run scripts from the skill folder.

## Structure

```text
android-skills/
├── android-ui/
│   ├── SKILL.md
│   ├── references/
│   └── scripts/
├── opencode/
│   └── commands/
├── bin/
│   ├── android-skills.js   (npm/npx wrapper)
│   └── postinstall.js      (global installs only)
├── tests/run_tests.py
├── package.json
├── install.py
├── README.md        (English)
└── README.id.md     (Bahasa Indonesia)
```

References and scripts are not loaded automatically when a skill is mentioned. The skills instruct the agent to read the relevant references and run the necessary scripts.

## Scripts

```bash
python3 android-ui/scripts/lint_ui.py app/src/main
python3 android-ui/scripts/contrast.py "#5B5D58" "#F7F7F5"   # always quote hex colors
python3 android-ui/scripts/validate_tokens.py "#3B5BA9" --package com.example.app
# with --write: refuses to overwrite an existing Color.kt/Theme.kt unless --force

python3 android-ui/scripts/scan.py app --format md --out security-report.md
python3 android-ui/scripts/scan.py app --fail-on high
```

The script paths above are relative to the extracted folder. After installing, run scripts via the skill installation path or the path OpenCode provides.

## Tests

```bash
python3 install.py --validate     # frontmatter + every referenced file exists
python3 tests/run_tests.py        # scripts + install/uninstall for all 7 targets
```

Suppress a scanner finding with `// sec-ignore: RULE_ID reason` (a reason is required) and a lint rule with `// ui-ignore: RULE_ID reason`.
`scan.py` exits 2 (not 0) when the path is wrong or holds no source files, so an empty scan is never reported as clean.

## Limitations

- `scan.py` is pattern-based. It does not track data flow and may produce false positives or miss vulnerabilities.
- `lint_ui.py` catches measurable violations; visual quality still requires human review.
- Audit results do not guarantee the app is safe and are not a substitute for a pentest or backend review.
- API recommendations can change. Verify the official documentation for the Android/AndroidX versions you use.



