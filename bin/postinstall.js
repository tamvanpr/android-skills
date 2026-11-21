#!/usr/bin/env node
"use strict";
/**
 * postinstall hook: auto-install the skill into the global OpenCode config,
 * but ONLY for a global install (npm i -g). Local installs, npx runs and
 * development checkouts are left alone so nothing is written to ~/.config
 * as a surprise.
 *
 * Opt out:  ANDROID_SKILLS_SKIP_POSTINSTALL=1
 * Force:    ANDROID_SKILLS_FORCE_POSTINSTALL=1
 *
 * This never fails the npm install; it reports what happened instead.
 */
const { spawnSync } = require("child_process");
const fs = require("fs");
const path = require("path");

const env = process.env;
if (env.ANDROID_SKILLS_SKIP_POSTINSTALL) process.exit(0);
const isGlobal = env.npm_config_global === "true" || env.npm_config_location === "global";
if (!isGlobal && !env.ANDROID_SKILLS_FORCE_POSTINSTALL) {
  console.log("[android-skills] Local install: nothing was written. Run `npx android-skills --help` to install into an agent.");
  process.exit(0);
}

function findPython() {
  for (const cand of process.platform === "win32" ? ["py", "python", "python3"] : ["python3", "python"]) {
    const r = spawnSync(cand, ["--version"], { stdio: "ignore" });
    if (r.status === 0 && !r.error) return cand;
  }
  return null;
}

const py = findPython();
if (!py) {
  console.log(
    "\n[android-skills] python3 was not found, so the skill was not installed automatically.\n" +
    "[android-skills] Install Python (e.g. `pkg install python`), then run: android-skills\n"
  );
  process.exit(0);
}

const script = path.join(__dirname, "..", "install.py");
if (!fs.existsSync(script)) {
  console.log("\n[android-skills] install.py is missing; run manually: android-skills");
  process.exit(0);
}

const r = spawnSync(py, [script], { stdio: "inherit" });
console.log(
  r.status === 0
    ? "\n[android-skills] android-ui skill installed into the OpenCode global config.\n[android-skills] Restart your OpenCode session to pick it up."
    : "\n[android-skills] Automatic install failed; run manually: android-skills"
);
process.exit(0);
