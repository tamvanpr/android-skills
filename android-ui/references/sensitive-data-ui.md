# Sensitive data in the UI layer

Sensitive data: passwords, PINs, OTPs, tokens, card numbers, health data, identity, private messages.

## Screenshots and recents

```kotlin
window.setFlags(WindowManager.LayoutParams.FLAG_SECURE, WindowManager.LayoutParams.FLAG_SECURE)
```

- Set it on login, OTP, PIN, payment, and any screen showing personal data.
- Set it in `onCreate` before `setContent`. Clear it on non-sensitive screens if the flag is set on a shared Activity.
- FLAG_SECURE also hides content from the recents preview and screen recording.
- On Android 13+ (API 33), `setRecentsScreenshotEnabled(false)` hides the recents preview without blocking screenshots.

## Clipboard

- Do not automatically copy passwords, tokens, or OTPs.
- If there is a "copy" button for sensitive data (the sensitive flag is honored on API 33+; clear the clipboard on older versions):
  ```kotlin
  val clip = ClipData.newPlainText("label", value).apply {
      description.extras = PersistableBundle().apply {
          putBoolean("android.content.extra.IS_SENSITIVE", true)
      }
  }
  ```
  And clear the clipboard after a short delay.
- Do not read the clipboard without a user action.

## Input fields

- Password: `PasswordVisualTransformation`, `KeyboardType.Password`, `autoCorrect = false`.
- OTP and PIN: `KeyboardType.NumberPassword`.
- Disable keyboard suggestions for secret fields (`autoCorrectEnabled = false`).
- XML: `android:inputType="textPassword"`, `android:importantForAutofill` as needed.
- Autofill: allow legitimate password managers, but disable it for one-time fields that do not need it (`importantForAutofill="no"`).

## State and processes

- Do not store secrets in `rememberSaveable`, `SavedStateHandle`, or `onSaveInstanceState`. Bundles survive and can be read elsewhere.
- Clear sensitive ViewModel state on logout and when the screen is dismissed.
- A `Parcelable` with tokens passed between Activities can appear in logs or dumps. Pass an ID, not the secret value.

## Logs

- Never log tokens, passwords, OTPs, or full response bodies.
- Use a logger that is a no-op in release (the Timber tree is planted in debug only).
- Remove `println` and `Log.*` from the authentication path.
- R8 can remove `Log.d/v` with `-assumenosideeffects`, but do not make that your only defense.

## Notifications

- Do not show sensitive content on the lock screen: `setVisibility(NotificationCompat.VISIBILITY_PRIVATE)` with `setPublicVersion`.
- Do not embed tokens in notification PendingIntent extras.

## Errors and messages

- User-facing error messages are generic. Technical details only in debug logs.
- Login: the same message for "account does not exist" and "wrong password".

## Images and display

- Image caches (Coil, Glide) can keep sensitive images on disk. Disable disk caching for identity-document images, or clear them on logout.
- Do not show full sensitive data if not needed: mask card numbers, show only the last 4 digits.

## Biometrics

- Use `BiometricPrompt` with a `CryptoObject` for actions that guard a key, not just a "success" boolean.
- Do not store an "authenticated" status in a variable that can be tampered on rooted devices without server-side verification.

## Logout

Cleanup checklist: tokens, ViewModels, disk and memory caches, WebView cookies, `WebStorage`, clipboard, notifications, local databases with user data, preferences.
