# Safe WebView

## Principles

Treat all web content as untrusted unless it comes from your app's own assets. The more capabilities you give the WebView, the bigger the blast radius of one XSS.

## Base configuration

```kotlin
fun WebView.hardened() {
    settings.apply {
        javaScriptEnabled = false            // enable only if needed
        allowFileAccess = false
        allowContentAccess = false
        allowFileAccessFromFileURLs = false
        allowUniversalAccessFromFileURLs = false
        mixedContentMode = WebSettings.MIXED_CONTENT_NEVER_ALLOW
        setSupportMultipleWindows(false)
        safeBrowsingEnabled = true
        domStorageEnabled = false            // enable only if needed
        javaScriptCanOpenWindowsAutomatically = false
    }
}
```

## Load local content with WebViewAssetLoader

```kotlin
val loader = WebViewAssetLoader.Builder()
    .addPathHandler("/assets/", WebViewAssetLoader.AssetsPathHandler(context))
    .build()

webView.webViewClient = object : WebViewClient() {
    override fun shouldInterceptRequest(view: WebView, request: WebResourceRequest) =
        loader.shouldInterceptRequest(request.url)
}
webView.loadUrl("https://appassets.androidplatform.net/assets/index.html")
```

Avoid `file:///android_asset/` for content that uses JavaScript.

## Navigation allowlist

```kotlin
private val allowedHosts = setOf("example.com", "appassets.androidplatform.net")

override fun shouldOverrideUrlLoading(view: WebView, req: WebResourceRequest): Boolean {
    val uri = req.url
    val ok = uri.scheme == "https" && uri.host in allowedHosts
    if (!ok) { /* open in an external browser or refuse */ }
    return !ok
}
```

Check hosts with full matching. Never `host.endsWith("example.com")`, because `evilexample.com` passes. Use `host == d || host.endsWith(".$d")`.

## JS-to-Kotlin bridge

Safer option than `addJavascriptInterface`:

```kotlin
if (WebViewFeature.isFeatureSupported(WebViewFeature.WEB_MESSAGE_LISTENER)) {
    WebViewCompat.addWebMessageListener(
        webView, "bridge", setOf("https://appassets.androidplatform.net"),
    ) { _, message, origin, _, reply -> /* validate message.data */ }
}
```

If you must keep `addJavascriptInterface`:
- Only for local content you control.
- Methods annotated with `@JavascriptInterface`, as few as possible.
- Validate every argument as untrusted input.
- Do not expose sensitive capabilities (files, credentials, intents).

## SSL errors

```kotlin
override fun onReceivedSslError(v: WebView, h: SslErrorHandler, e: SslError) {
    h.cancel()           // never proceed()
}
```

## Cookies and storage

- Clear cookies, cache, and `WebStorage` on logout.
- Do not keep tokens in the WebView's `localStorage` if avoidable.
- `CookieManager.setAcceptThirdPartyCookies(webView, false)`.

## Downloads and permissions

- Handle `setDownloadListener` with type and source validation.
- Refuse `onPermissionRequest` (camera, microphone) except from trusted origins.
- Refuse `onShowFileChooser` from untrusted origins.

## Compose

An `AndroidView` wrapping a WebView inherits all risks above. Create the WebView in `factory`, release it in `onRelease` (`destroy()`), and do not hold references to the Activity.

## Anti-patterns

- `loadUrl(intent.data.toString())` without validation.
- `evaluateJavascript("setName('$name')")` with a user-supplied `name`.
- `setJavaScriptEnabled(true)` + `addJavascriptInterface` + loading external URLs.
- Ignoring `onReceivedSslError` so "the test works".
- WebView debugging enabled in release.
