# Report template

Use this format. Short, specific, actionable. No emoji.

```
# UI security review report: <app name>

Date: <date>
Scope: <modules, variant, targetSdk>
Method: automated scan (scan.py) + manual review of <area>
Not checked: <backend, native code, third-party SDKs, etc.>

## Summary
<2–4 sentences: number of findings per level, the most urgent item>

| Level | Count | Confirmed | False positive |
|---|---|---|---|

## Findings

### [HIGH] W-INTERFACE: addJavascriptInterface on a WebView that loads external URLs
- Location: app/src/main/java/.../HelpScreen.kt:84
- Status: confirmed | possible | false positive
- Impact: a compromised page could call `bridge.*` methods and read <what>
- Scenario: <minimal, conceptual steps, on your own app>
- Fix: <concrete change + short code example>
- Notes: <side effects, API level>

(repeat per finding, ordered critical to info)

## What is already good
<short, evidence-based: e.g. "every exported component has a permission">

## Further recommendations
<out of scope: pentest, backend review, dependencies>
```

## Rating severity

Rate with two questions:

1. **Exploitability**
   - Easy: another app on the device or a web page can trigger it without special interaction
   - Moderate: needs user interaction or a specific condition
   - Hard: needs physical access, root, or a chain of weaknesses
2. **Impact**
   - High: credential leak, code execution, account takeover, fund loss
   - Moderate: limited data leak, feature bypass
   - Low: technical information, hardening

| Impact \ Ease | Easy | Moderate | Hard |
|---|---|---|---|
| High | critical | high | medium |
| Moderate | high | medium | low |
| Low | medium | low | info |

Adjustments:
- Debug source set only: downgrade one level and note whether it can leak into release.
- App processes financial, health, or identity data: upgrade one level for data leaks.
- App with no user data and no accounts: downgrade one level for hardening.
- Low confidence (possible false positive): still report it as "possible" and explain what to check.

## Handling secrets

If you find a secret, write only the first four characters and its type in the report ("AIza****", Google API key). Recommend rotation before other fixes.

## After fixing

- Re-run `scan.py` and compare finding counts.
- Run the release build and test the touched flows.
- Note findings deliberately suppressed with `sec-ignore`, with the reason.
