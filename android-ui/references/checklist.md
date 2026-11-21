# Android UI security checklist

IDs are used by `scripts/scan.py` and by reports. For each item: risk, how to check, fix.

## A. WebView

| ID | Risk | Check | Fix |
|---|---|---|---|
| W-JS | XSS becomes code execution in the app with untrusted content | `javaScriptEnabled` | Enable only for trusted content |
| W-INTERFACE | Web page calls Kotlin code | `addJavascriptInterface` | Minimal methods, local content only, or WebMessageListener with origin restrictions |
| W-FILE / W-FILE2 | Read local files from a malicious page | `allowFileAccess*`, `allowUniversalAccessFromFileURLs` | Disable, use `WebViewAssetLoader` |
| W-MIXED | http content injected into an https page | `MIXED_CONTENT_ALWAYS_ALLOW` | `NEVER_ALLOW` |
| W-SSL | MITM | `onReceivedSslError` + `proceed()` | `cancel()` |
| W-DEBUG | WebView inspection in release | `setWebContentsDebuggingEnabled(true)` | Debug only |
| W-LOADURL-HTTP / W-LOADURL-DYN | Loading http or untrusted URLs | `loadUrl("http://...")`, `loadUrl(variable)` | HTTPS, allowlist schemes and hosts |
| W-LOADDATA | Untrusted data interpolated into HTML | `loadData*` with interpolation | Escape, or do not build HTML |
| W-CONTENT | Content provider access from WebView | `allowContentAccess` | Disable if not needed |
| W-EVALJS | Script injection | `evaluateJavascript` with a built string | JSON escaping, `postWebMessage` |

## B. Components and intents

| ID | Risk | Check | Fix |
|---|---|---|---|
| M-EXPORT-IMPLICIT | Component opened by accident | intent-filter without `exported` | Set it explicitly |
| M-EXPORT | Other apps can trigger the component | `exported="true"` | Signature permission, or false |
| M-PROVIDER / M-GRANT | Data leak | exported provider, grantUriPermissions | Restrict paths and permissions |
| M-APPLINK | Link hijacking | https without `autoVerify` | Verified App Links |
| M-DEEPLINK | Untrusted input | BROWSABLE intent-filter | Validate parameters |
| C-REDIRECT | Intent redirection | Launching an Intent taken from an extra | Validate the target, strip URI flags |
| C-PENDING | Intent modified by another app | PendingIntent without flags | `FLAG_IMMUTABLE`, explicit Intent |
| C-RECEIVER | Receiver exposed | `registerReceiver` | `RECEIVER_NOT_EXPORTED` |
| C-BROADCAST | Data leaks via broadcast | `sendBroadcast` | `setPackage`, permission |
| C-IMPLICIT | Opening arbitrary URIs | `ACTION_VIEW` + dynamic Uri | Validate scheme and host |
| C-FILEPROVIDER | Sharing more files than intended | root path in provider XML | Specific subfolder |
| M-PERM | Attack surface | Risky permissions | Remove, or use a safer API |

## C. Sensitive data in the UI

| ID | Risk | Check | Fix |
|---|---|---|---|
| U-SECURE | Screenshot and recents preview leak | No `FLAG_SECURE` on a sensitive screen | Set the flag per screen |
| U-TAPJACK | Overlay deceives the user | Sensitive button without touch filtering | `filterTouchesWhenObscured` |
| U-LOG | Data leaks via logcat | Logs containing tokens, passwords | Remove the logs, strip in release |
| U-STACKTRACE | Internal info leaks | `printStackTrace`, exception toasts | Generic message |
| U-CLIPBOARD | Other apps read the clipboard | `setPrimaryClip` with secret data | Avoid, mark as sensitive |
| U-SAVEABLE | Secrets in the Bundle | `rememberSaveable` + password | `remember` |
| U-AUTOFILL | Autofill sends data to a third-party service | `importantForAutofill="yes"` | Check sensitive fields manually |
| U-PWFIELD / U-INPUTTYPE | Password visible or cached by the keyboard | TextField without transformation | Transformation + keyboard type |

## D. Inputs and state

| ID | Risk | Check | Fix |
|---|---|---|---|
| I-SQL | SQL injection | `rawQuery` with a built string | Parameter binding |
| I-PATH | Path traversal | `File(...)` from input | canonicalPath + allowlist |
| I-DEEPLINK | Untrusted parameter | `getQueryParameter` | Validate |
| I-HTML | Rendering untrusted HTML | `Html.fromHtml` | Trusted source |
| I-RANDOM | Guessable tokens | `Random` | `SecureRandom` |
| I-HASH / I-CIPHER | Weak crypto | MD5, SHA-1, ECB | SHA-256, AES-GCM |

## E. Network and storage

| ID | Risk | Check | Fix |
|---|---|---|---|
| N-HTTP | Cleartext | `http://` URLs | HTTPS |
| M-CLEARTEXT / N-NSC-CLEAR | Global cleartext | Manifest, NSC | Disable |
| N-NSC-USER | User CAs trusted | `src="user"` | Debug only |
| N-TRUSTALL / N-HOSTNAME | Full MITM | Custom TrustManager and HostnameVerifier | Remove |
| N-PINNING | Certificate spoofing | OkHttp without pinning | Consider pinning |
| S-PREFS | Secrets readable | Plain SharedPreferences | Keystore encryption |
| S-WORLD | Files readable by other apps | `MODE_WORLD_*` | `MODE_PRIVATE` |
| S-EXTERNAL | Data on shared storage | External storage | Private storage |
| M-BACKUP | Data goes with backups | `allowBackup` | Disable, or exclude |
| M-DEBUGGABLE | Debugging in production | `debuggable` | Remove |

## F. Secrets

| ID | Check |
|---|---|
| S-SECRET | Literal values on variables named key, token, secret |
| S-PRIVKEY | Private key headers |
| S-AWS, S-TOKENFMT, S-GOOGLEKEY | Known token formats |

Rule: anything shipped to a client is public. Real secrets live on the server.

## Manual checks that cannot be automated

1. Are sensitive screens reachable only after authentication? What happens when the process is killed and reopened via a deep link?
2. Does logout clear state, image caches, WebView cookies, and the clipboard?
3. Do sensitive actions (transfer, delete account) require re-authentication or BiometricPrompt with CryptoObject?
4. Do error messages leak the difference between "user not found" and "wrong password"?
5. Is there security logic done only on the client (price check, role check)? It must be repeated on the server.
6. Are server-provided images or URLs loaded without size or scheme limits?
7. Do third-party libraries (WebView wrappers, ad SDKs) add permissions or exported components via manifest merge? Check the merged manifest (`app/build/intermediates/merged_manifests`).
8. Is ProGuard or R8 enabled for release, and does it not leak sensitive names?
