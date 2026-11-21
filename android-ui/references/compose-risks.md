# Jetpack Compose-specific risks

## Persisted state

- `rememberSaveable` stores values in the Bundle (restorable after process death, visible in debug tools). Do not use it for passwords, PINs, tokens.
- `SavedStateHandle` in a ViewModel carries the same risk.
- Use `remember` for secrets and clear it when the screen leaves composition (`DisposableEffect`).

```kotlin
var pin by remember { mutableStateOf("") }
DisposableEffect(Unit) { onDispose { pin = "" } }
```

JVM strings cannot be wiped from memory with certainty. Do not claim "safely deleted"; you only shortened the reference's lifetime.

## Text fields

```kotlin
OutlinedTextField(
    value = password,
    onValueChange = { password = it },
    visualTransformation = if (visible) VisualTransformation.None else PasswordVisualTransformation(),
    keyboardOptions = KeyboardOptions(
        keyboardType = KeyboardType.Password,
        autoCorrectEnabled = false,   // Compose UI 1.7+; older: autoCorrect = false
        imeAction = ImeAction.Done,
    ),
    singleLine = true,
)
```

- The show-password toggle is temporary. Hide it again when the screen loses focus or the app goes to background.
- Use `Modifier.semantics { password() }` so accessibility services and autofill treat it as a password.
- Limit input length (`onValueChange = { if (it.length <= 64) ... }`).

## Semantics and accessibility

- `contentDescription` and `stateDescription` are read by accessibility services. Do not put secret data in them.
- For content that must not be read by accessibility services, use `Modifier.clearAndSetSemantics { }` or `invisibleToUser()` carefully, while still providing an alternative for users who need it.
- A malicious accessibility service can read the screen. For the most sensitive screens, consider FLAG_SECURE and checking for active accessibility services.

## AndroidView and interop

- `AndroidView { WebView(it) }` inherits all WebView risks (see `webview.md`).
- Release resources in `onRelease`. Do not hold an Activity Context in long-lived objects.

## Navigation

- Route arguments are strings on the back stack and in deep links. Do not pass sensitive objects as arguments. Pass an ID, fetch data from the repository.
- `navDeepLink` exposes the route externally. Check authentication at the destination, not only on the first screen.
- Make sure `popUpTo` after login/logout clears the back stack so the user cannot return to a sensitive screen.

## Previews and sample data

- No real data, tokens, or internal URLs in `@Preview` or sample data. It ends up in the repo.
- Preview code ships in the APK unless wrapped in the debug source set. Use `debugImplementation` for preview tooling.

## Sensitive screens

- Set FLAG_SECURE on the host Activity. Compose single-activity means the flag applies to every screen. Set it dynamically per route:

```kotlin
@Composable
fun SecureScreen(content: @Composable () -> Unit) {
    val window = (LocalContext.current as Activity).window
    DisposableEffect(Unit) {
        window.addFlags(WindowManager.LayoutParams.FLAG_SECURE)
        onDispose { window.clearFlags(WindowManager.LayoutParams.FLAG_SECURE) }
    }
    content()
}
```

## Dialogs and overlays

- Compose dialogs create their own window. `DialogProperties(securePolicy = SecureFlagPolicy.SecureOn)` sets FLAG_SECURE for sensitive dialogs.
- Triggers for destructive or financial actions in dialogs are still vulnerable to tapjacking. See `components-intents.md`.

## Side effects

- A `LaunchedEffect` that sends data over the network based on user input can fire repeatedly on recomposition or configuration changes. Make effect keys correct so a sensitive action is not sent twice.

## Third-party UI libraries

- Review the permissions and components they add via manifest merge.
- Pin versions and track security updates. Avoid unmaintained libraries for sensitive tasks (WebView wrappers, QR scanners, card input).
