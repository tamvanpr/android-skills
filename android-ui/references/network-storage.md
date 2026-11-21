# Network and storage (UI perspective)

## Cleartext

- Manifest: do not set `usesCleartextTraffic="true"`.
- Target SDK 28+ blocks cleartext by default. Exceptions must go through `network_security_config` and stay narrow.
- All API, image, and WebView URLs use `https://`.

## network_security_config

Safe example for release:

```xml
<network-security-config>
    <base-config cleartextTrafficPermitted="false">
        <trust-anchors>
            <certificates src="system" />
        </trust-anchors>
    </base-config>
    <debug-overrides>
        <trust-anchors>
            <certificates src="user" />
        </trust-anchors>
    </debug-overrides>
</network-security-config>
```

Do not trust user CAs (`src="user"`) in release.

## Certificate pinning

For high-risk apps (finance, health), pinning reduces fake-CA risk. But:
- Pin to the public key (SPKI), include at least one backup.
- Have a rotation and expiry plan. A wrong pin makes the app unable to connect.
- Pinning is not a replacement for server validation.

```kotlin
val pinner = CertificatePinner.Builder()
    .add("api.example.com", "sha256/AAAA...=", "sha256/BBBB...=")
    .build()
```

## Custom TrustManager and HostnameVerifier

Never implement one that accepts all certificates or all hosts, including "temporarily for dev". For dev servers with self-signed certs, register the dev CA in `debug-overrides`.

## Storage

| Data type | Where |
|---|---|
| Session tokens | Encrypted private storage with an Android Keystore key |
| Non-sensitive preferences | DataStore or SharedPreferences |
| Image cache | Private cache, clear on logout |
| User files | `filesDir` (private) or SAF/MediaStore at the user's choice |

Note: `EncryptedSharedPreferences` from `androidx.security:security-crypto` is marked deprecated in recent releases. Check the version you use and consider Keystore directly, or Tink with an encrypted DataStore.

Rules:
- Store the minimum. Short-lived tokens + revocable refresh tokens.
- Encryption keys never in source or in assets.
- Use `setUserAuthenticationRequired(true)` for keys guarding the most sensitive data.
- Do not store passwords. Store tokens.

## Backups

- `android:allowBackup="false"`, or define `dataExtractionRules` (Android 12+) and `fullBackupContent` excluding databases, tokens, and sensitive preferences.

## Files and shared storage

- Avoid writing sensitive data to external storage or MediaStore.
- Delete temporary files after use.
- Be careful with file names from the server or from users.

## Secrets in the app

- Anything in the APK can be extracted: strings, resources, BuildConfig, assets, native libraries.
- API keys that must live on the client (maps, analytics) must be restricted provider-side (package name + SHA-1, API allowlist, quotas).
- Full-access secrets (server keys, cloud service keys) do not belong on the client. Move them to the backend or a proxy.
- If one was committed: revoke and rotate first, then clean git history.
- For BYOK apps (the user enters their own API key): store encrypted in Keystore, do not log, do not put in crash reports, do not send anywhere except the intended provider, mask when displayed.

## Release

- Enable R8 (`isMinifyEnabled = true`) and `isShrinkResources` for release.
- Sign with a key stored securely, not in the repo.
- Ensure `debuggable` is false, logging off, WebView debugging off.
- Use the Play Integrity API where needed, with server-side verification.
