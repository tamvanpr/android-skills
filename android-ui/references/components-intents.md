# Components, intents, deep links

## Exported

Since target SDK 31, components with an `intent-filter` require an explicit `android:exported`. Rules:
- Default `false`. Change to `true` only when other apps must call it.
- A launcher activity must be exported. Other activities usually are not.
- Exported services, receivers, and providers must be protected with `android:permission` (signature) unless intentionally public.
- Check the merged manifest, because libraries can add exported components.

## Activities receiving data from outside

Treat `intent.extras`, `intent.data`, and `intent.action` as untrusted input.

```kotlin
val id = intent.getStringExtra("id")?.takeIf { it.matches(Regex("[A-Za-z0-9_-]{1,64}")) }
    ?: return finish()
```

Do not:
- Pass an extra directly into a query, file path, WebView URL, or `startActivity`.
- Assume the extra type is correct. Use the typed API version (`getParcelableExtra(key, Clazz::class.java)`) and handle null.
- Trust `callingPackage` as authentication.

## Intent redirection

Dangerous pattern:

```kotlin
val forward = intent.getParcelableExtra<Intent>("next")
startActivity(forward)   // attacker picks the destination, including private components
```

Fix: do not accept an Intent in extras. If unavoidable, resolve it and restrict the destination to an allowlist of components, strip `FLAG_GRANT_*_URI_PERMISSION`, and do not launch with elevated rights.

## Deep links

- Validate scheme, host, path, and every parameter.
- Use verified App Links (`autoVerify="true"`, `assetlinks.json`) for https.
- Custom schemes can be hijacked by other apps. Never send tokens over a custom scheme.
- Do not skip authentication just because the entry came from a deep link. Check the session before showing a sensitive screen.
- Be careful with `redirect`, `url`, `next` parameters. Allowlist destinations to prevent open redirects.
- Navigation Compose arguments from deep links are still untrusted input.

## PendingIntent

- Always set `FLAG_IMMUTABLE` unless it truly must be filled in later (`FLAG_MUTABLE`).
- The intent inside is explicit (component or package set). No empty Intent.
- For notifications, do not embed sensitive data in extras.

## Broadcasts

- `registerReceiver` on Android 13+ requires `RECEIVER_NOT_EXPORTED` for internal broadcasts.
- `sendBroadcast` with sensitive data: restrict to your own package (`setPackage`) or use a permission.
- Consider in-process alternatives (Flow, SharedFlow) instead of broadcasts.

## FileProvider and file sharing

- Define paths as narrow as possible, never `root-path` or `.`
- Use `FileProvider.getUriForFile`, not `Uri.fromFile`.
- Grant `FLAG_GRANT_READ_URI_PERMISSION` only to a specific receiver on the Intent being sent; do not make the provider exported.
- Validate user-supplied file names (strip `..`, path separators) before writing.

## Sharing and receiving content

- `ACTION_SEND` activities receive text or Uris from any app. Validate size, MIME type, and Uri scheme (`content` only, not `file`).
- Copy into private storage before processing. Do not open `content://` with a path from input.

## Tapjacking

Screens that trigger sensitive actions with a single tap can be overlaid.
- Views: `filterTouchesWhenObscured = true`.
- Compose: read `LocalView.current` and set the same property on the root view, or check `MotionEvent.FLAG_WINDOW_IS_OBSCURED` and refuse the action.
- For critical confirmations, add an explicit step (a dialog with clear text).
