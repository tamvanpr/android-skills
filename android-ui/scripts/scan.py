#!/usr/bin/env python3
"""Static scanner for Android frontend/UI security risks (Kotlin, Java, XML, Manifest).

This is a pattern-based scanner, not data-flow analysis. Every finding must
be verified manually. Rule IDs match references/checklist.md.

Usage:
  python3 scan.py <path> [--format text|md|json] [--out FILE]
                  [--min-severity info|low|medium|high|critical]
                  [--fail-on high] [--include-tests]

Suppress a finding with a comment (a reason is required, otherwise it is ignored):
  // sec-ignore: RULE_ID reason
(in AndroidManifest.xml: <!-- sec-ignore: RULE_ID reason -->, directly above the element)
Exit code: 1 if any finding >= --fail-on, 2 on bad input or nothing scanned, else 0.
"""
import argparse
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter

SEV = ["info", "low", "medium", "high", "critical"]
SKIP_DIRS = {"build", ".git", ".gradle", ".idea", ".cxx", "node_modules", "generated"}
TEST_DIRS = {"test", "androidTest", "testDebug", "sharedTest"}
CODE_EXT = (".kt", ".java", ".kts", ".gradle")
ANDROID_NS = "{http://schemas.android.com/apk/res/android}"
IGNORE = re.compile(r"sec-ignore:\s*([A-Z0-9-]+)[ \t]*([^\n]*)")


def suppressed(ctx, rid):
    """True if ctx holds `sec-ignore: RID <reason>`. A suppression without a reason does not count."""
    for m in IGNORE.finditer(ctx):
        reason = m.group(2).replace("-->", "").replace("*/", "").strip()
        if m.group(1) == rid and len(reason) >= 3:
            return True
    return False
SENS = r"(password|passwd|token|secret|otp|\bpin\b|cvv|api[_-]?key)"


class Rule:
    def __init__(self, rid, sev, title, pat, advice, kinds="code", neg=None, need=None,
                 window=0, conf="medium", flags=0):
        self.rid, self.sev, self.title, self.advice = rid, sev, title, advice
        self.kinds, self.conf, self.window = kinds, conf, window
        self.pat = re.compile(pat, flags)
        self.neg = re.compile(neg, flags) if neg else None
        self.need = re.compile(need, flags) if need else None


I = re.I
RULES = [
    # WebView
    Rule("W-JS", "medium", "JavaScript enabled in WebView",
         r"setJavaScriptEnabled\(\s*true\s*\)|javaScriptEnabled\s*=\s*true",
         "Enable only when needed and only for trusted content. Restrict the origins loaded."),
    Rule("W-INTERFACE", "high", "addJavascriptInterface",
         r"addJavascriptInterface\(",
         "Only for trusted local content. Annotate a minimal set of methods with @JavascriptInterface, or use a WebMessageListener with allowedOriginRules."),
    Rule("W-FILE", "high", "WebView file access too loose",
         r"(setAllowUniversalAccessFromFileURLs|setAllowFileAccessFromFileURLs)\(\s*true|allow(UniversalAccessFromFileURLs|FileAccessFromFileURLs)\s*=\s*true",
         "Disable. Load local assets through WebViewAssetLoader."),
    Rule("W-FILE2", "medium", "allowFileAccess enabled",
         r"setAllowFileAccess\(\s*true|allowFileAccess\s*=\s*true",
         "Turn off, or use WebViewAssetLoader."),
    Rule("W-CONTENT", "medium", "allowContentAccess enabled",
         r"setAllowContentAccess\(\s*true|allowContentAccess\s*=\s*true",
         "Turn off unless content providers are needed."),
    Rule("W-MIXED", "high", "Mixed content allowed",
         r"MIXED_CONTENT_ALWAYS_ALLOW", "Use MIXED_CONTENT_NEVER_ALLOW and HTTPS only."),
    Rule("W-DEBUG", "medium", "WebView debugging enabled",
         r"setWebContentsDebuggingEnabled\(\s*true",
         "Guard with BuildConfig.DEBUG or (applicationInfo.flags and FLAG_DEBUGGABLE)."),
    Rule("W-LOADURL-HTTP", "high", "WebView loads an http URL",
         r"(loadUrl|loadDataWithBaseURL)\(\s*\"http://", "Use HTTPS."),
    Rule("W-LOADURL-DYN", "low", "loadUrl with a dynamic value",
         r"\.loadUrl\(\s*[^\"\s)]", "Make sure the URL is validated against a scheme and host allowlist before loading.",
         neg=r"javascript:", conf="low"),
    Rule("W-LOADDATA", "medium", "loadData with interpolation",
         r"(loadData|loadDataWithBaseURL)\(.*(\$\{?\w|\+\s*\w)",
         "Escape, or avoid interpolating untrusted data into HTML."),
    Rule("W-EVALJS", "medium", "evaluateJavascript with interpolation",
         r"evaluateJavascript\(.*(\$\{?\w|\"\s*\+|\+\s*\")",
         "Send data via escaped JSON or postWebMessage, do not build strings."),
    Rule("W-HOSTCHECK", "medium", "Host allowlist check with endsWith",
         r"\b(host|authority)\W{0,4}endsWith\(",
         'endsWith("example.com") also accepts evilexample.com. Compare host == d || host.endsWith(".$d").'),
    Rule("W-SSL", "critical", "SSL error ignored in WebView",
         r"onReceivedSslError", "Do not call handler.proceed(). Call cancel().",
         need=r"\.proceed\(\)", window=6),
    # Components and intents
    Rule("C-REDIRECT", "medium", "Possible intent redirection",
         r"getParcelableExtra(<Intent>)?\(|getParcelable(<Intent>)?\(.*Intent",
         "Do not launch an Intent received from outside. Validate the target component and strip URI permission flags.",
         need=r"Intent", conf="low"),
    Rule("C-PENDING", "high", "PendingIntent without a mutability flag",
         r"PendingIntent\.get(Activity|Broadcast|Service|Activities|ForegroundService)\(",
         "Add FLAG_IMMUTABLE (or FLAG_MUTABLE only when truly needed) and an explicit Intent.",
         neg=r"FLAG_IMMUTABLE|FLAG_MUTABLE", window=3),
    Rule("C-RECEIVER", "medium", "registerReceiver without an export flag",
         r"registerReceiver\(", "On Android 13+ set RECEIVER_NOT_EXPORTED unless it is meant for other apps.",
         neg=r"RECEIVER_NOT_EXPORTED|RECEIVER_EXPORTED", window=2),
    Rule("C-BROADCAST", "low", "sendBroadcast without a receiver limit",
         r"sendBroadcast\(", "Use setPackage or a receiver permission so data does not leak to other apps.",
         neg=r"setPackage|permission|Permission", window=2, conf="low"),
    Rule("C-IMPLICIT", "medium", "startActivity with an implicit Intent from dynamic data",
         r"Intent\(\s*Intent\.ACTION_VIEW\s*,\s*Uri\.parse\(\s*[^\"\s)]",
         "Validate the Uri scheme and host before opening. Handle ActivityNotFoundException.", conf="low"),
    Rule("C-URIFILE", "low", "Uri.fromFile used",
         r"Uri\.fromFile\(", "Use FileProvider.getUriForFile; file:// Uris throw FileUriExposedException when shared."),
    Rule("C-FILEPROVIDER", "high", "FileProvider opens a root path",
         r"<root-path|<external-path\s+[^>]*path=\"\.?/?\"", "Restrict FileProvider paths to a specific subfolder.", kinds="xml"),
    # Sensitive data in the UI
    Rule("U-LOG", "high", "Sensitive data written to logs",
         r"(Log\.[dviwe]|Timber\.[dviwe]|println)\s*\(.*" + SENS,
         "Remove the log or do not include sensitive values. Make sure debug logging is stripped in release.", flags=I),
    Rule("U-STACKTRACE", "low", "printStackTrace and exception messages to the UI",
         r"printStackTrace\(\)|Toast\.makeText\(.*(\.message|\.localizedMessage|\.toString\(\))",
         "Log concisely via a logger disabled in release. Show a generic message to the user."),
    Rule("U-CLIPBOARD", "medium", "Sensitive data copied to the clipboard",
         r"(setPrimaryClip|ClipData\.newPlainText)\(.*" + SENS,
         "Avoid copying sensitive data. If needed, mark ClipDescription.EXTRA_IS_SENSITIVE and clear it automatically.", flags=I),
    Rule("U-SAVEABLE", "medium", "Sensitive data stored in rememberSaveable",
         r"(rememberSaveable.*" + SENS + r"|" + SENS + r".*rememberSaveable)",
         "State is persisted to the Bundle and can survive process death. Use plain remember for secrets.", flags=I),
    Rule("U-PWFIELD", "medium", "Password field without transformation or keyboard type",
         r"\b(Outlined)?(Basic)?TextField\(", "Use PasswordVisualTransformation and KeyboardType.Password. Consider a temporary show toggle.",
         need=r"password|passwd|kata sandi", neg=r"PasswordVisualTransformation|KeyboardType\.(Password|NumberPassword)",
         window=25, flags=I),
    Rule("U-INPUTTYPE", "medium", "Sensitive EditText without a password inputType",
         r"<EditText|<com\.google\.android\.material\.textfield\.TextInputEditText", "Set android:inputType=\"textPassword\" for secret fields.",
         kinds="xml", need=r"password|pin|otp", neg=r"inputType=\"[^\"]*(Password|numberPassword)", window=8, flags=I, conf="low"),
    Rule("U-AUTOFILL", "info", "AutoFill enabled manually",
         r"importantForAutofill\s*=\s*\"yes\"", "Make sure sensitive fields do not send data to an unwanted third-party autofill service.", kinds="xml"),
    # Secrets
    Rule("S-SECRET", "high", "Hardcoded secret",
         r"(api[_-]?key|secret|passwd|password|token|bearer|client[_-]?secret)\w*\s*(=|:)\s*\"(?=[A-Za-z_\-/+=.]*\d)(?=[0-9_\-/+=.]*[A-Za-z])[A-Za-z0-9_\-/+=.]{16,}\"",
         "Do not store secrets in the APK. Move them to the backend or a proxy. Rotate any key that was already committed.",
         kinds="all", neg=r"BuildConfig|R\.string|getString|stringResource|example|your_|changeme|xxxx", flags=I, conf="low"),
    Rule("S-PRIVKEY", "critical", "Private key in source",
         r"-----BEGIN (RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----", "Remove from the repo, rotate, and clean git history.", kinds="all"),
    Rule("S-AWS", "critical", "AWS access key",
         r"\bAKIA[0-9A-Z]{16}\b", "Revoke and rotate immediately.", kinds="all"),
    Rule("S-GOOGLEKEY", "medium", "Google API key in source",
         r"\bAIza[0-9A-Za-z_\-]{35}\b", "Restrict the key in the console (package name + SHA-1, API allowlist). Do not use an unrestricted key.", kinds="all"),
    Rule("S-TOKENFMT", "high", "Token in a known format",
         r"\b(ghp_[A-Za-z0-9]{36}|xox[baprs]-[A-Za-z0-9-]{10,}|sk-[A-Za-z0-9]{32,})\b", "Revoke and rotate.", kinds="all"),
    # Storage
    Rule("S-PREFS", "medium", "Sensitive data in plain SharedPreferences",
         r"(putString|edit\(\).*put\w+)\(\s*\"[^\"]*" + SENS, "Store secrets with Android Keystore-backed encryption (check the current recommendation for the encryption library in use).", flags=I),
    Rule("S-WORLD", "high", "World-readable/writable file mode",
         r"MODE_WORLD_(READABLE|WRITEABLE)", "Use MODE_PRIVATE."),
    Rule("S-EXTERNAL", "low", "External storage",
         r"getExternalStorageDirectory\(|Environment\.getExternalStorage", "Do not store sensitive data on external storage. Use the app's private storage."),
    # Network
    Rule("N-HTTP", "medium", "http URL (cleartext)",
         r"\"http://(?!localhost|127\.0\.0\.1|10\.0\.2\.2|schemas\.android\.com|www\.w3\.org|schemas\.microsoft)", "Use HTTPS.", kinds="all"),
    Rule("N-HOSTNAME", "critical", "HostnameVerifier accepts everything",
         r"ALLOW_ALL_HOSTNAME_VERIFIER|HostnameVerifier\s*\{[^}]*\btrue\b|hostnameVerifier\s*\{\s*_\s*,\s*_\s*->\s*true",
         "Remove. Use the default verification."),
    Rule("N-TRUSTALL", "critical", "TrustManager accepts everything",
         r"object\s*:\s*X509TrustManager|implements\s+X509TrustManager|new\s+X509TrustManager", "Do not implement a custom TrustManager that bypasses validation. Use network_security_config or CertificatePinner.",
         need=r"checkServerTrusted\s*\([^)]*\)\s*(:\s*\w+\s*)?\{\s*(//[^\n]*\n\s*)*\}", window=12),
    Rule("N-PINNING", "info", "OkHttp without a CertificatePinner (check manually)",
         r"OkHttpClient\.Builder\(\)", "For high-risk apps, consider certificate pinning with a rotation strategy.",
         neg=r"certificatePinner|CertificatePinner", window=15, conf="low"),
    # Inputs and injection
    Rule("I-SQL", "high", "SQL built from strings",
         r"(rawQuery|execSQL|SimpleSQLiteQuery)\(.*(\+\s*\w|\$\{?\w)", "Use parameter binding (?) or Room with a parameterized @Query."),
    Rule("I-PATH", "medium", "File path from external input",
         r"File\(.*( getStringExtra|getQueryParameter|lastPathSegment|\.path\b|getString\()",
         "Normalize with canonicalPath and make sure it stays inside an allowed directory. Reject '..'.", conf="low"),
    Rule("I-DEEPLINK", "info", "Deep link parameter used",
         r"getQueryParameter\(|intent\??\.data\b|intent\??\.getStringExtra\(", "Validate type, length, and value. Do not use it directly for navigation or queries.", conf="low"),
    Rule("I-HTML", "low", "Html.fromHtml from dynamic data",
         r"Html\.fromHtml\(\s*[^\"\s)]", "Make sure the source is trusted. Avoid rendering HTML from user input.", conf="low"),
    Rule("I-RANDOM", "medium", "Non-crypto Random for security values",
         r"\bjava\.util\.Random\(|\bRandom\(\)|Math\.random\(\)", "Use SecureRandom for tokens, OTPs, nonces.",
         need=r"token|otp|session|password|nonce|key", window=3, flags=I),
    Rule("I-HASH", "medium", "Weak hash",
         r"MessageDigest\.getInstance\(\s*\"(MD5|SHA-?1)\"\s*\)", "Use SHA-256 or stronger. For passwords use a server-side KDF."),
    Rule("I-CIPHER", "high", "Weak cipher or ECB mode",
         r"Cipher\.getInstance\(\s*\"(AES|DES|DESede|RC4|Blowfish)(/ECB/\w+)?\"\s*\)", "Use AES/GCM/NoPadding with a random IV per message."),
]

PROJECT_NOTES = []


def walk(root, include_tests):
    if os.path.isfile(root):
        yield root
        return
    for d, dirs, files in os.walk(root):
        dirs[:] = [x for x in dirs if x not in SKIP_DIRS and (include_tests or x not in TEST_DIRS)]
        for f in files:
            if f.endswith(CODE_EXT + (".xml",)):
                yield os.path.join(d, f)


def kind_ok(rule, path):
    is_xml = path.endswith(".xml")
    if rule.kinds == "all":
        return True
    return is_xml if rule.kinds == "xml" else not is_xml


def find_line(text, needle):
    idx = text.find(needle)
    return text.count("\n", 0, idx) + 1 if idx >= 0 else 1


def scan_lines(path, text, findings):
    lines = text.splitlines()
    for rule in RULES:
        if not kind_ok(rule, path):
            continue
        for i, line in enumerate(lines):
            s = line.strip()
            if s.startswith(("//", "*", "/*", "<!--")):
                continue
            if not rule.pat.search(line):
                continue
            win = "\n".join(lines[i:i + 1 + rule.window])
            if rule.need and not rule.need.search(win):
                continue
            if rule.neg and rule.neg.search(win if rule.window else line):
                continue
            ctx = "\n".join(lines[max(0, i - 1):i + 1])
            if suppressed(ctx, rule.rid):
                continue
            findings.append(dict(rule=rule.rid, severity=rule.sev, title=rule.title, file=path,
                                 line=i + 1, snippet=s[:160], advice=rule.advice, confidence=rule.conf))


def is_debug_path(path):
    return "/debug/" in path.replace("\\", "/")


def scan_manifest(path, text, findings):
    mlines = text.splitlines()

    def add(rid, sev, title, needle, advice, conf="high"):
        ln = find_line(text, needle)
        ctx = "\n".join(mlines[max(0, ln - 3):ln])
        if suppressed(ctx, rid):
            return
        if is_debug_path(path) and sev in ("high", "medium"):
            sev = "info"
            title += " (debug source set)"
        findings.append(dict(rule=rid, severity=sev, title=title, file=path, line=ln,
                             snippet=needle[:160], advice=advice, confidence=conf))

    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        return
    app = root.find("application")
    if app is not None:
        if app.get(ANDROID_NS + "debuggable") == "true":
            add("M-DEBUGGABLE", "high", "debuggable=true", "android:debuggable", "Remove the attribute. Let the build type decide.")
        if app.get(ANDROID_NS + "allowBackup") == "true":
            add("M-BACKUP", "medium", "allowBackup=true", "android:allowBackup",
                "Set false, or define dataExtractionRules and fullBackupContent that exclude sensitive data.")
        is_real_app = any(app.get(ANDROID_NS + k) for k in ("label", "icon", "name"))
        if is_real_app and app.get(ANDROID_NS + "allowBackup") is None and not app.get(ANDROID_NS + "dataExtractionRules"):
            add("M-BACKUP", "medium", "allowBackup not set (the default is true)", "<application",
                "Set allowBackup=false, or define dataExtractionRules (Android 12+) and fullBackupContent.", "medium")
        if app.get(ANDROID_NS + "usesCleartextTraffic") == "true":
            add("M-CLEARTEXT", "high", "usesCleartextTraffic=true", "android:usesCleartextTraffic", "Set false and use HTTPS.")
        for comp in app:
            tag = comp.tag
            if tag not in ("activity", "activity-alias", "service", "receiver", "provider"):
                continue
            name = comp.get(ANDROID_NS + "name", "?")
            exported = comp.get(ANDROID_NS + "exported")
            perm = comp.get(ANDROID_NS + "permission")
            filters = comp.findall("intent-filter")
            launcher = any(c.get(ANDROID_NS + "name") == "android.intent.category.LAUNCHER"
                           for f in filters for c in f.findall("category"))
            if filters and exported is None:
                add("M-EXPORT-IMPLICIT", "high", f"{tag} with an intent-filter and no android:exported ({name})", name,
                    "Android 12+ requires the attribute explicitly. Set true only if it is meant for other apps.")
            if exported == "true" and not launcher:
                if tag == "activity" or tag == "activity-alias":
                    add("M-EXPORT", "medium", f"Exported activity ({name})", name,
                        "Validate all intent extras and data. Consider a permission or exported=false.", "medium")
                elif not perm and tag != "provider":
                    add("M-EXPORT", "high", f"{tag} exported without a permission ({name})", name,
                        "Set exported=false or protect it with a signature-level permission.")
            if tag == "provider":
                if exported == "true":
                    add("M-PROVIDER", "high", f"Exported ContentProvider ({name})", name,
                        "Set exported=false, or protect it with readPermission/writePermission and restrict the paths.")
                if comp.get(ANDROID_NS + "grantUriPermissions") == "true":
                    add("M-GRANT", "medium", f"grantUriPermissions=true ({name})", name,
                        "Restrict with <grant-uri-permission> on specific paths.", "medium")
            for f in filters:
                cats = {c.get(ANDROID_NS + "name") for c in f.findall("category")}
                datas = f.findall("data")
                if "android.intent.category.BROWSABLE" in cats and datas:
                    schemes = {d.get(ANDROID_NS + "scheme") for d in datas if d.get(ANDROID_NS + "scheme")}
                    web = bool(schemes & {"http", "https"})
                    if web and f.get(ANDROID_NS + "autoVerify") != "true":
                        add("M-APPLINK", "low", f"Web link without autoVerify ({name})", name,
                            "Use verified Android App Links (assetlinks.json) so it cannot be hijacked by another app.", "medium")
                    add("M-DEEPLINK", "info", f"Deep link {sorted(schemes)} ({name})", name,
                        "Treat all parameters as untrusted input.", "medium")
    risky = {
        "SYSTEM_ALERT_WINDOW": ("medium", "The overlay permission increases tapjacking and UI phishing risk."),
        "MANAGE_EXTERNAL_STORAGE": ("medium", "All-files access. Use SAF or MediaStore."),
        "REQUEST_INSTALL_PACKAGES": ("low", "Make sure installing packages is truly needed."),
        "READ_EXTERNAL_STORAGE": ("low", "Consider the Photo Picker or SAF."),
        "WRITE_EXTERNAL_STORAGE": ("low", "Consider MediaStore or SAF."),
        "READ_SMS": ("medium", "Use the SMS Retriever API for OTPs."),
        "RECEIVE_SMS": ("medium", "Use the SMS Retriever API for OTPs."),
    }
    for up in root.findall("uses-permission"):
        n = (up.get(ANDROID_NS + "name") or "").split(".")[-1]
        if n in risky:
            sev, adv = risky[n]
            add("M-PERM", sev, f"Permission {n}", n, adv, "medium")


def scan_nsc(path, text, findings):
    debug_start = text.find("<debug-overrides")
    debug_end = text.find("</debug-overrides>")
    for m in re.finditer(r'cleartextTrafficPermitted\s*=\s*"true"', text):
        findings.append(dict(rule="N-NSC-CLEAR", severity="high", title="network_security_config allows cleartext",
                             file=path, line=text.count("\n", 0, m.start()) + 1, snippet=m.group(0),
                             advice="Set false. Only exclude specific dev domains in debug-overrides.", confidence="high"))
    for m in re.finditer(r'<certificates\s+src\s*=\s*"user"', text):
        in_debug = debug_start != -1 and debug_start < m.start() < (debug_end if debug_end != -1 else len(text))
        findings.append(dict(rule="N-NSC-USER", severity="info" if in_debug else "medium",
                             title="User certificate trust anchor" + (" (debug-overrides)" if in_debug else ""),
                             file=path, line=text.count("\n", 0, m.start()) + 1, snippet=m.group(0),
                             advice="Do not trust user CAs in release.", confidence="high"))


def project_checks(files_text, findings):
    sensitive = [p for p, t in files_text.items()
                 if re.search(r"PasswordVisualTransformation|KeyboardType\.(Password|NumberPassword)|textPassword|numberPassword", t)]
    if sensitive:
        all_text = "\n".join(files_text.values())
        if "FLAG_SECURE" not in all_text and "setSecure" not in all_text:
            findings.append(dict(rule="U-SECURE", severity="medium", title="Sensitive screen without FLAG_SECURE",
                                 file=sensitive[0], line=1, snippet="(project level: FLAG_SECURE not found)",
                                 advice="Set WindowManager.LayoutParams.FLAG_SECURE on login, OTP, PIN, and payment screens to block screenshots and the recents preview.",
                                 confidence="medium"))
        if not re.search(r"filterTouchesWhenObscured|FLAG_WINDOW_IS_OBSCURED|MotionEvent\.FLAG_WINDOW_IS_PARTIALLY_OBSCURED", all_text):
            findings.append(dict(rule="U-TAPJACK", severity="low", title="No tapjacking protection",
                                 file=sensitive[0], line=1, snippet="(project level)",
                                 advice="For sensitive action buttons, set filterTouchesWhenObscured=true (Views) or check the obscured flags on touch events in Compose.",
                                 confidence="low"))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path")
    ap.add_argument("--format", choices=["text", "md", "json"], default="text")
    ap.add_argument("--out")
    ap.add_argument("--min-severity", choices=SEV, default="info")
    ap.add_argument("--fail-on", choices=SEV)
    ap.add_argument("--include-tests", action="store_true")
    a = ap.parse_args()
    if not os.path.exists(a.path):
        print(f"error: path not found: {a.path}", file=sys.stderr)
        sys.exit(2)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass

    findings, files_text = [], {}
    for path in walk(a.path, a.include_tests):
        try:
            with open(path, encoding="utf-8", errors="replace") as fh:
                text = fh.read()
        except OSError:
            continue
        files_text[path] = text
        base = os.path.basename(path)
        if base == "AndroidManifest.xml":
            scan_manifest(path, text, findings)
        elif path.endswith(".xml") and "<network-security-config" in text:
            scan_nsc(path, text, findings)
        scan_lines(path, text, findings)
    project_checks(files_text, findings)
    if not files_text:
        print("error: no .kt/.java/.kts/.gradle/.xml files found under " + a.path
              + ". Nothing was scanned, so this is NOT a clean result.", file=sys.stderr)
        sys.exit(2)

    floor = SEV.index(a.min_severity)
    findings = [f for f in findings if SEV.index(f["severity"]) >= floor]
    findings.sort(key=lambda f: (-SEV.index(f["severity"]), f["file"], f["line"]))
    counts = Counter(f["severity"] for f in findings)

    if a.format == "json":
        body = json.dumps({"counts": counts, "files_scanned": len(files_text), "findings": findings}, indent=2, ensure_ascii=False)
    elif a.format == "md":
        out = ["# Android UI security scan report", "",
               f"Files scanned: {len(files_text)}", "",
               "| Severity | Count |", "|---|---|"]
        out += [f"| {s} | {counts.get(s, 0)} |" for s in reversed(SEV)]
        out += ["", "This scanner is pattern-based. Verify every finding manually before drawing conclusions.", ""]
        for f in findings:
            out += [f"## [{f['severity'].upper()}] {f['rule']}: {f['title']}", "",
                    f"- Location: `{f['file']}:{f['line']}`",
                    f"- Confidence: {f['confidence']}",
                    f"- Snippet: `{f['snippet']}`",
                    f"- Fix: {f['advice']}", ""]
        body = "\n".join(out)
    else:
        out = []
        for f in findings:
            out.append(f"[{f['severity'].upper():8}] {f['rule']:18} {f['file']}:{f['line']}  ({f['confidence']})")
            out.append(f"    {f['title']}")
            out.append(f"    > {f['snippet']}")
            out.append(f"    -> {f['advice']}")
        out.append("")
        out.append("Summary: " + ", ".join(f"{counts.get(s, 0)} {s}" for s in reversed(SEV))
                   + f" | files scanned: {len(files_text)}")
        body = "\n".join(out)

    if a.out:
        with open(a.out, "w", encoding="utf-8") as fh:
            fh.write(body + "\n")
        print(f"Report written to {a.out} ({len(findings)} findings)")
    else:
        print(body)

    if a.fail_on and any(SEV.index(f["severity"]) >= SEV.index(a.fail_on) for f in findings):
        sys.exit(1)


if __name__ == "__main__":
    main()
