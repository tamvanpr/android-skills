#!/usr/bin/env python3
"""Installer for the Android skill, for a range of AI agents.

Supported: opencode (default), claude, codex, gemini, copilot, cursor, windsurf.

Usage:
  python3 install.py                                 # OpenCode global
  python3 install.py --project .                     # OpenCode project
  python3 install.py --target claude --project .     # Claude Code project
  python3 install.py --target cursor                 # Cursor global
  python3 install.py --target codex --project .      # Codex: .android-skills/ + block in AGENTS.md
  python3 install.py --target gemini --project .     # Gemini CLI: GEMINI.md
  python3 install.py --target copilot --project .    # GitHub Copilot: .github/copilot-instructions.md
  python3 install.py --link                          # symlink instead of a copy
  python3 install.py --agents-md                      # write the instructions block into the rules file (skills mode)
  python3 install.py --uninstall
  python3 install.py --validate

OpenCode & Claude Code use the skill layout  <root>/skills/<name>/SKILL.md .
Cursor & Windsurf use rules files in  <root>/rules/ .
Codex, Gemini CLI, and Copilot use instruction files (AGENTS.md, GEMINI.md,
copilot-instructions.md) plus the skill folder in <root>/.android-skills/ (project)
or <root>/android-skills/ (global).
"""
import argparse
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILLS = ["android-ui"]
SKILL_SUMMARY = {
    "android-ui": "builds/polishes Android UIs and audits the UI/frontend security layer",
}
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
BEGIN, END = "<!-- android-skills:begin -->", "<!-- android-skills:end -->"
COMMANDS = ("ui.md",)
# Old names from earlier versions, cleaned up on uninstall.
LEGACY_SKILLS = ["android-ui-minimal", "android-ui-security-review"]
LEGACY_COMMANDS = ("ui-minimal.md", "ui-security.md")

TARGETS = {
    "opencode": dict(
        desc="OpenCode", mode="skills", commands=True,
        global_base=lambda: os.path.join(os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config"), "opencode"),
        project_base=".opencode", rules="AGENTS.md",
    ),
    "claude": dict(
        desc="Claude Code", mode="skills", commands=False,
        global_base=lambda: os.path.expanduser("~/.claude"),
        project_base=".claude", rules="CLAUDE.md",
    ),
    "codex": dict(
        desc="Codex CLI", mode="instructions", commands=False,
        global_base=lambda: os.path.expanduser("~/.codex"),
        project_base=None, rules="AGENTS.md",
    ),
    "gemini": dict(
        desc="Gemini CLI", mode="instructions", commands=False,
        global_base=lambda: os.path.expanduser("~/.gemini"),
        project_base=None, rules="GEMINI.md",
    ),
    "copilot": dict(
        desc="GitHub Copilot", mode="instructions", commands=False,
        global_base=None,
        project_base=".github", rules=".github/copilot-instructions.md",
    ),
    "cursor": dict(
        desc="Cursor", mode="rules", commands=False,
        global_base=lambda: os.path.expanduser("~/.cursor"),
        project_base=".cursor", rules_dir="rules", rules_ext=".mdc",
    ),
    "windsurf": dict(
        desc="Windsurf", mode="rules", commands=False,
        global_base=lambda: os.path.expanduser("~/.windsurf"),
        project_base=".windsurf", rules_dir="rules", rules_ext=".md",
    ),
}


def frontmatter(path):
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    text = text.replace("\r\n", "\n")
    m = re.match(r"^---\n(.*?)\n---(?:\n|$)", text, re.S)
    if not m:
        return None
    data, key, buf = {}, None, []

    def flush():
        if key is not None:
            data[key] = " ".join(x for x in buf if x).strip()

    for line in m.group(1).splitlines():
        top = re.match(r"^([A-Za-z_-]+):[ \t]*(.*)$", line)
        if top:
            flush()
            key, v = top.group(1), top.group(2).strip()
            buf = [] if v in (">", "|", ">-", "|-", "") else [v.strip("\"'")]
        elif key is not None and line[:1] in (" ", "\t"):
            buf.append(line.strip())  # folded/literal scalar or nested map line
    flush()
    return data


def validate():
    ok = True
    for s in SKILLS:
        md = os.path.join(HERE, s, "SKILL.md")
        if not os.path.isfile(md):
            print(f"FAIL {s}: SKILL.md not found")
            ok = False
            continue
        fm = frontmatter(md)
        if not fm:
            print(f"FAIL {s}: frontmatter not found")
            ok = False
            continue
        name, desc = fm.get("name", ""), fm.get("description", "")
        problems = []
        if name != s:
            problems.append(f"name '{name}' must equal the folder name '{s}'")
        if not (1 <= len(name) <= 64 and NAME_RE.match(name)):
            problems.append("name must be lowercase letters, digits, and single hyphens (1-64)")
        if not (1 <= len(desc) <= 1024):
            problems.append(f"description must be 1-1024 characters (currently {len(desc)})")
        body = open(md, encoding="utf-8").read()
        for ref in sorted(set(re.findall(r"`((?:references|scripts)/[\w./-]+\.(?:md|py))`", body))):
            if not os.path.isfile(os.path.join(HERE, s, ref)):
                problems.append(f"SKILL.md mentions {ref}, but the file does not exist")
        for p in problems:
            print(f"FAIL {s}: {p}")
        ok &= not problems
        if not problems:
            print(f"OK    {s} (description {len(desc)} chars)")
    return ok


def put(src, dst, link):
    if os.path.lexists(dst):
        if os.path.islink(dst) or os.path.isfile(dst):
            os.remove(dst)
        else:
            shutil.rmtree(dst)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if link:
        os.symlink(src, dst)
    elif os.path.isdir(src):
        shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    else:
        shutil.copy2(src, dst)


def managed_block(skills_dir, start_at):
    """Managed instructions block for rules files (AGENTS.md, CLAUDE.md, etc.)."""
    rel = lambda p: os.path.relpath(p, start_at)
    lines = [
        BEGIN,
        "",
        "## Android UI skill",
        "",
        "The `android-ui` skill is available for Android work:",
        f"- UI mode: build/polish the UI. SKILL.md: `{rel(os.path.join(skills_dir, 'android-ui', 'SKILL.md'))}`",
        f"- References and scripts (lint_ui.py, contrast.py, validate_tokens.py, scan.py) live next to it: `{rel(os.path.join(skills_dir, 'android-ui'))}/references` and `/scripts`. Run scripts from that path, not from the project folder.",
        "- Security mode: audit the UI/frontend layer (read-only unless asked to fix).",
        "",
        "Rules:",
        "- Before UI work or a security audit on Android, read the `android-ui` SKILL.md and the relevant references.",
        "- Verify compilation/tests before pushing; one commit one thing; do not roll back a design to make CI green.",
        "- No emoji in UI, strings, comments, or commits. Ask first when the request is ambiguous.",
        "",
        END,
    ]
    return "\n".join(lines) + "\n"


def update_managed_file(path, skills_dir, remove=False):
    text = open(path, encoding="utf-8").read() if os.path.exists(path) else ""
    text = re.sub(re.escape(BEGIN) + r".*?" + re.escape(END) + r"\n?", "", text, flags=re.S)
    if not remove:
        text = (text.rstrip("\n") + "\n\n" if text.strip() else "") + managed_block(skills_dir, os.path.dirname(path))
    if remove and not text.strip():
        if os.path.exists(path):
            os.remove(path)
        return
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def with_always_apply(md_text):
    m = re.match(r"^---\n(.*?)\n---\n?", md_text, re.S)
    if not m:
        return md_text
    fm, body = m.group(1), md_text[m.end():]
    if not re.search(r"^alwaysApply:", fm, re.M):
        fm += "\nalwaysApply: false"
    return f"---\n{fm}\n---\n{body}"


def make_rule_file(skill, dst, skills_dir, ext):
    """Create a rules file (.mdc for Cursor, .md for Windsurf) from SKILL.md."""
    text = open(os.path.join(HERE, skill, "SKILL.md"), encoding="utf-8").read().replace("\r\n", "\n")
    text = with_always_apply(text)
    note = f"\n> Full skill folder (references & scripts) is at: {os.path.relpath(os.path.join(skills_dir, skill), start=os.path.dirname(dst))}\n"
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(dst, "w", encoding="utf-8") as fh:
        fh.write(text + note)


def layout(t, project):
    """Compute target locations based on the mode."""
    if t["mode"] == "skills":
        base = os.path.join(project, t["project_base"]) if project else t["global_base"]()
        skills_dir = os.path.join(base, "skills")
        cmd_dir = os.path.join(base, "commands") if t.get("commands") else None
        rules_path = os.path.join(project if project else base, t["rules"])
        return dict(base=base, skills_dir=skills_dir, cmd_dir=cmd_dir,
                    rules_path=rules_path, rules_dir=None, rules_ext=None)
    if t["mode"] == "rules":
        base = os.path.join(project, t["project_base"]) if project else t["global_base"]()
        rules_dir = os.path.join(base, t["rules_dir"])
        skills_dir = os.path.join(base, "skills")
        return dict(base=base, skills_dir=skills_dir, cmd_dir=None,
                    rules_path=None, rules_dir=rules_dir, rules_ext=t["rules_ext"])
    # mode instructions
    if project:
        base = project
        skills_dir = os.path.join(base, ".android-skills")
    else:
        if t["global_base"] is None:
            raise SystemExit(f"target '{t['desc']}' only supports --project DIR (e.g. --project .)")
        base = t["global_base"]()
        skills_dir = os.path.join(base, "android-skills")
    return dict(base=base, skills_dir=skills_dir, cmd_dir=None,
                rules_path=os.path.join(base, t["rules"]), rules_dir=None, rules_ext=None)


def remove_skill_dir(p):
    if os.path.lexists(p):
        if os.path.isdir(p) and not os.path.islink(p):
            shutil.rmtree(p)
        else:
            os.remove(p)
        print(f"removed: {p}")


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", metavar="DIR", help="install per-project into DIR (global path if omitted)")
    ap.add_argument("--target", choices=sorted(TARGETS), default="opencode",
                   help="target agent (default: opencode)")
    ap.add_argument("--link", action="store_true", help="symlink instead of a copy")
    ap.add_argument("--agents-md", action="store_true",
                    help="write/remove the instructions block in the target rules file "
                         "(AGENTS.md, CLAUDE.md, GEMINI.md, copilot-instructions.md). "
                         "For rules targets (cursor/windsurf) the rules file is always created.")
    ap.add_argument("--uninstall", action="store_true")
    ap.add_argument("--validate", action="store_true")
    a = ap.parse_args()

    if not validate():
        sys.exit(1)
    if a.validate:
        return

    t = TARGETS[a.target]
    L = layout(t, a.project)
    skills_dir = L["skills_dir"]
    rules_dir = L["rules_dir"]
    rules_ext = L["rules_ext"]
    rules_path = L["rules_path"]
    mode = t["mode"]

    if a.uninstall:
        for s in SKILLS:
            remove_skill_dir(os.path.join(skills_dir, s))
        if L.get("cmd_dir"):
            for c in COMMANDS + LEGACY_COMMANDS:
                p = os.path.join(L["cmd_dir"], c)
                if os.path.lexists(p):
                    os.remove(p)
                    print(f"removed: {p}")
            legacy_dir = os.path.join(L["base"], "command")
            for c in COMMANDS + LEGACY_COMMANDS:
                p = os.path.join(legacy_dir, c)
                if os.path.lexists(p):
                    os.remove(p)
                    print(f"removed (legacy): {p}")
        if rules_dir:
            for s in SKILLS:
                p = os.path.join(rules_dir, s + rules_ext)
                if os.path.lexists(p):
                    os.remove(p)
                    print(f"removed: {p}")
            for s in LEGACY_SKILLS:
                p = os.path.join(rules_dir, s + rules_ext)
                if os.path.lexists(p):
                    os.remove(p)
                    print(f"removed (old name): {p}")
        # clean up leftovers from older installs (separate skills)
        for s in LEGACY_SKILLS:
            p = os.path.join(skills_dir, s)
            if os.path.lexists(p):
                if os.path.isdir(p) and not os.path.islink(p):
                    shutil.rmtree(p)
                else:
                    os.remove(p)
                print(f"removed (old version): {p}")
        if mode == "instructions":
            existed = os.path.exists(rules_path)
            update_managed_file(rules_path, skills_dir, remove=True)
            print(f"block removed from: {rules_path}" if existed else "no old block found")
            if os.path.isdir(skills_dir) and not os.listdir(skills_dir):
                os.rmdir(skills_dir)
                print(f"removed: {skills_dir}")
        elif a.agents_md and rules_path and os.path.exists(rules_path):
            update_managed_file(rules_path, skills_dir, remove=True)
            print(f"block removed from: {rules_path}")
        print("Uninstall complete.")
        return

    for s in SKILLS:
        dst = os.path.join(skills_dir, s)
        put(os.path.join(HERE, s), dst, a.link)
        print(f"installed: {dst}")
        scripts = os.path.join(dst, "scripts")
        if os.path.isdir(scripts) and not os.path.islink(dst):
            for f in os.listdir(scripts):
                if f.endswith(".py"):
                    try:
                        os.chmod(os.path.join(scripts, f), 0o755)
                    except OSError:
                        pass
    if L.get("cmd_dir"):
        for c in COMMANDS:
            put(os.path.join(HERE, "opencode", "commands", c), os.path.join(L["cmd_dir"], c), a.link)
            print(f"installed: {os.path.join(L['cmd_dir'], c)}")

    if rules_dir:
        for s in SKILLS:
            p = os.path.join(rules_dir, s + rules_ext)
            make_rule_file(s, p, skills_dir, rules_ext)
            print(f"installed: {p}")
    elif mode == "instructions":
        update_managed_file(rules_path, skills_dir)
        print(f"instructions updated: {rules_path}")
    elif a.agents_md:
        update_managed_file(rules_path, skills_dir)
        print(f"rules updated: {rules_path}")

    other = {"opencode": ".claude", "claude": ".opencode"}.get(a.target)
    if other and not a.link:
        root = a.project if a.project else os.path.expanduser("~")
        alt = os.path.join(root, other if a.project else (".claude" if a.target == "opencode" else os.path.join(".config", "opencode")), "skills", "android-ui")
        if os.path.exists(alt):
            print(f"\nNote: another copy exists at {alt}. OpenCode also reads .claude/skills, "
                  "so the same skill name may be loaded twice. Keep one copy (--uninstall the other).")

    rel_hint = {"opencode": "OpenCode", "claude": "Claude Code", "codex": "Codex",
                "gemini": "Gemini CLI", "copilot": "Copilot", "cursor": "Cursor",
                "windsurf": "Windsurf"}[a.target]
    print(f"\nDone ({rel_hint}). Restart the agent session if needed.")
    if L.get("cmd_dir"):
        print("Optional OpenCode command: /ui <screen|folder> (the mode is picked from the arguments)")
    if rules_dir:
        print("Rules file installed in " + rules_dir +
              " — make sure rules are enabled; global user rules may need to be added via the agent UI.")


if __name__ == "__main__":
    main()
