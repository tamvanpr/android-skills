#!/usr/bin/env node
"use strict";
/**
 * npx wrapper for android-skills.
 * Runs install.py with the same arguments.
 *
 * Examples:
 *   npx tamvanpr/android-skills --target claude --project .
 *   npx tamvanpr/android-skills --target cursor
 *   npm i -g android-skills && android-skills --help
 *
 * Note: the installer is written in Python (requires python3 on the machine).
 * If python3 is missing, an installation message is shown.
 */
const { spawnSync } = require("child_process");
const fs = require("fs");
const path = require("path");

function findPython() {
  for (const cand of process.platform === "win32" ? ["py", "python", "python3"] : ["python3", "python"]) {
    const r = spawnSync(cand, ["--version"], { stdio: "ignore" });
    if (r.status === 0 && !r.error) return cand;
  }
  return null;
}

const py = findPython();
if (!py) {
  console.error(
    "python3 not found in PATH.\n" +
    "The android-skills installer is written in Python.\n" +
    "Options:\n" +
    "  1) Install Python: pkg install python / apt install python3 / winget install Python.Python.3.12\n" +
    "  2) Or clone the repo directly: git clone https://github.com/tamvanpr/android-skills && python3 install.py --help"
  );
  process.exit(1);
}

const script = path.join(__dirname, "..", "install.py");
if (!fs.existsSync(script)) {
  console.error("install.py not found at " + script);
  process.exit(1);
}

const args = process.argv.slice(2);
const r = spawnSync(py, [script, ...args], { stdio: "inherit" });
process.exit(r.status === null ? 1 : r.status);
