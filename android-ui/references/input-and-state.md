# Inputs and state from outside

Any value not produced directly by your code is untrusted: user input, intent extras, deep links, network responses, file contents, clipboard, `ContentResolver` results, navigation arguments, QR contents.

## Validation

- Validate at the entry boundary (ViewModel or use case), not scattered across composables.
- Use allowlists, not blocklists: length, characters, ranges, enums.
- Parse into strong types as early as possible (`UUID`, `Int`, `enum`), handle failures.
- Client validation is for UX only. The server still re-validates.

```kotlin
fun parseAmount(raw: String): Long? =
    raw.takeIf { it.length <= 12 && it.all(Char::isDigit) }?.toLongOrNull()
        ?.takeIf { it in 1..100_000_000 }
```

## Injection

| Context | Risk | Prevent |
|---|---|---|
| SQLite | SQL injection | Parameter binding, Room |
| WebView | XSS, JS injection | Do not build HTML/JS, escaped JSON |
| Intent / URI | Redirection, open redirect | Allowlist schemes and hosts |
| File | Path traversal | `canonicalPath` + base directory |
| Regex | ReDoS | Avoid nested-iteration patterns on user input, limit length |
| String format | Leaks | Never use user input as the format |

Path traversal:

```kotlin
val base = File(context.filesDir, "uploads").canonicalFile
val target = File(base, name).canonicalFile
require(target.path.startsWith(base.path + File.separator)) { "invalid path" }
```

## Deep links and navigation arguments

```kotlin
composable("detail/{id}") { entry ->
    val id = entry.arguments?.getString("id")?.toLongOrNull() ?: return@composable
    // check authorization: may this user see this id?
}
```

An ID in a URL is not authorization. Check access rights on the server (IDOR).

## QR and camera content

- Treat as untrusted URLs. Show the destination to the user before opening.
- Restrict schemes (`https`). Do not open `intent://` or `javascript:`.

## Network responses

- Use typed data models, ignore unknown fields, handle missing fields.
- Limit response sizes and the number of items rendered.
- Do not render HTML from responses unless sanitized.
- Server-provided image URLs: allow https only, limit decode size (`size(...)` in Coil).

## Displayed text

- User text shown in `Text` is safe from HTML injection. Risk appears when using `Html.fromHtml`, `AnnotatedString` from markup, or WebView.
- Limit text length and lines (`maxLines`, `overflow`) so the layout does not break.
- Watch for bidirectional control characters in file names or usernames shown in confirmation UIs.

## Races and state

- Prevent double submission on sensitive actions: disable the button while in flight, use an idempotency key on the server.
- Do not decide security from UI state (`isAdmin` in the ViewModel). The server decides.
- After process death, UI state can be restored with stale values. Re-verify the session before sensitive actions.

## Client-side validation that is often wrong

- Hiding a button is not access control.
- Obfuscation (R8) is not encryption.
- Root or emulator detection is not a security boundary.
- Client-only PIN attempt limiting can be bypassed.
