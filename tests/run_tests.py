#!/usr/bin/env python3
"""Self-tests for the android-ui scripts and the installer. Run: python3 tests/run_tests.py"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "android-ui", "scripts")


def write(path, text):
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def run(*args):
    p = subprocess.run([sys.executable, *args], capture_output=True, text=True, encoding="utf-8")
    return p.returncode, p.stdout + p.stderr


MANIFEST = """<manifest xmlns:android="http://schemas.android.com/apk/res/android">
  <application android:label="x">
    <activity android:name=".Main"><intent-filter>
      <action android:name="android.intent.action.MAIN"/>
      <category android:name="android.intent.category.LAUNCHER"/></intent-filter></activity>
    <service android:name=".Svc" android:exported="true"/>
  </application>
</manifest>"""

BAD_KT = '''package com.x
@Composable fun Login() {
    var password by rememberSaveable { mutableStateOf("") }
    Text("Hi", fontSize = 17.sp, modifier = Modifier.padding(13.dp))
    Box(Modifier.background(Color(0xFF123456)))
    IconButton(onClick = {}, modifier = Modifier.size(32.dp)) {}
    OutlinedTextField(value = password, onValueChange = { password = it })
    w.settings.javaScriptEnabled = true
    return !r.url.host!!.endsWith("example.com")
    val u = Uri.fromFile(f)
    // sec-ignore: S-WORLD
    val a = openFileOutput("a", MODE_WORLD_READABLE)
    // sec-ignore: S-WORLD legacy file, never shared
    val b = openFileOutput("b", MODE_WORLD_READABLE)
}
'''


class Scripts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        main = os.path.join(cls.tmp.name, "app", "src", "main")
        os.makedirs(os.path.join(main, "java"))
        write(os.path.join(main, "AndroidManifest.xml"), MANIFEST)
        write(os.path.join(main, "java", "A.kt"), BAD_KT)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_lint_rules_fire(self):
        code, out = run(os.path.join(SCRIPTS, "lint_ui.py"), self.tmp.name)
        self.assertEqual(code, 1)
        for rule in ("FONT_SIZE", "HEX_COLOR", "DP_OFF_SCALE", "TOUCH_TARGET"):
            self.assertIn(rule, out)

    def test_lint_ignore_needs_rule_id(self):
        p = os.path.join(self.tmp.name, "B.kt")
        write(p, '// ui-ignore: FONT_SIZE brand display text\nText("x", fontSize = 17.sp)\n')
        code, out = run(os.path.join(SCRIPTS, "lint_ui.py"), p)
        self.assertNotIn("FONT_SIZE ", out.replace("FONT_SIZE_XML", ""))

    def test_scan_rules_fire(self):
        code, out = run(os.path.join(SCRIPTS, "scan.py"), self.tmp.name, "--format", "json")
        data = json.loads(out)
        rules = {f["rule"] for f in data["findings"]}
        for r in ("M-EXPORT", "M-EXPORT-IMPLICIT", "M-BACKUP", "U-SAVEABLE", "U-PWFIELD",
                  "W-JS", "W-HOSTCHECK", "C-URIFILE"):
            self.assertIn(r, rules, r)

    def test_scan_suppression_requires_reason(self):
        code, out = run(os.path.join(SCRIPTS, "scan.py"), self.tmp.name, "--format", "json")
        lines = [f["line"] for f in json.loads(out)["findings"] if f["rule"] == "S-WORLD"]
        self.assertEqual(len(lines), 1, "only the suppression without a reason may remain")

    def test_scan_fail_on_and_bad_path(self):
        self.assertEqual(run(os.path.join(SCRIPTS, "scan.py"), self.tmp.name, "--fail-on", "high")[0], 1)
        self.assertEqual(run(os.path.join(SCRIPTS, "scan.py"), "/no/such/dir")[0], 2)
        with tempfile.TemporaryDirectory() as empty:
            self.assertEqual(run(os.path.join(SCRIPTS, "scan.py"), empty)[0], 2)

    def test_contrast(self):
        self.assertEqual(run(os.path.join(SCRIPTS, "contrast.py"), "#000000", "#FFFFFF")[0], 0)
        self.assertEqual(run(os.path.join(SCRIPTS, "contrast.py"), "#777777", "#888888")[0], 1)
        self.assertEqual(run(os.path.join(SCRIPTS, "contrast.py"), "zzz", "#FFFFFF")[0], 2)

    def test_validate_tokens_write_guards(self):
        v = os.path.join(SCRIPTS, "validate_tokens.py")
        self.assertNotEqual(run(v, "#3B5BA9", "--write")[0], 0)  # --write without --out
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(run(v, "#3B5BA9", "--out", d, "--write")[0], 0)
            self.assertTrue(os.path.isfile(os.path.join(d, "Color.kt")))
            self.assertEqual(run(v, "#3B5BA9", "--out", d, "--write")[0], 1)  # no silent overwrite
            self.assertEqual(run(v, "#3B5BA9", "--out", d, "--write", "--force")[0], 0)


class Installer(unittest.TestCase):
    def test_validate_reads_folded_description(self):
        code, out = run(os.path.join(ROOT, "install.py"), "--validate")
        self.assertEqual(code, 0, out)
        self.assertNotIn("description 1 chars", out)

    def test_install_and_uninstall_every_target(self):
        for target in ("opencode", "claude", "codex", "gemini", "copilot", "cursor", "windsurf"):
            with self.subTest(target=target), tempfile.TemporaryDirectory() as proj:
                code, out = run(os.path.join(ROOT, "install.py"), "--target", target, "--project", proj)
                self.assertEqual(code, 0, out)
                found = [os.path.join(d, "SKILL.md") for d, _, fs in os.walk(proj) if "SKILL.md" in fs]
                self.assertTrue(found, f"no SKILL.md installed for {target}")
                self.assertTrue(os.path.isfile(os.path.join(os.path.dirname(found[0]), "scripts", "scan.py")))
                code, out = run(os.path.join(ROOT, "install.py"), "--target", target, "--project", proj, "--uninstall")
                self.assertEqual(code, 0, out)
                left = [d for d, _, fs in os.walk(proj) if "SKILL.md" in fs]
                self.assertFalse(left, f"leftovers after uninstall for {target}: {left}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
