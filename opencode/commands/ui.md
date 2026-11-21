---
description: Android UI work (build/reconstruct/polish) or frontend security audit, using the android-ui skill
---

Load the `android-ui` skill (OpenCode ID: `@android-ui`), pick the mode from the arguments below, and follow the skill's workflow.

Arguments: $ARGUMENTS

- If the arguments mention a screen/UI/redesign/tidying → **UI mode**.
- If the arguments mention audit/security/hardening → **Security mode** (read-only unless asked to fix).
- If empty, infer from the conversation context; if still ambiguous, ask one thing first.

If the target is clear, proceed without re-asking what is already known. Read the relevant references from the skill directory. Run the relevant automated checks (linter, contrast, or security scanner). Follow the safety rules: verify compilation/tests BEFORE pushing, one commit one thing, fix forward instead of rolling back. Change only the requested scope. Report the files changed, the checks that ran (and the ones that could not run), and their limits.
