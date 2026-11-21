# Android Skills

Satu skill untuk pekerjaan Android: `android-ui`, dengan dua mode: **UI** (membangun, merekonstruksi, merapikan UI) dan **security** (audit lapisan UI/frontend). Mendukung OpenCode, Claude Code, Codex CLI, Gemini CLI, GitHub Copilot, Cursor, dan Windsurf.

## Instalasi

```bash
# langsung dari repo (tanpa clone); butuh python3
npx tamvanpr/android-skills --target claude --project .

# global; otomatis memasang ke OpenCode (~/.config/opencode)
npm i -g android-skills

# via git / ZIP
python3 install.py
```

Flag: `--project DIR`, `--target`, `--link`, `--agents-md`, `--uninstall`, `--validate`.

Catatan:
- Hook postinstall hanya jalan untuk instalasi global. Instal lokal dan `npx` tidak menulis apa pun ke `~/.config`. Nonaktifkan dengan `ANDROID_SKILLS_SKIP_POSTINSTALL=1`.
- OpenCode juga membaca `.claude/skills`. Pasang di salah satu lokasi saja agar nama skill tidak ganda.
- Di Termux: `pkg install python git`.

## Pemakaian

```text
@android-ui
Rapikan layar pengaturan. Pertahankan semua fungsi dan state.
```

```text
@android-ui
Audit keamanan frontend di app/src/main. Jangan ubah file; laporkan temuan dan false positive.
```

Referensi dan skrip tidak dimuat otomatis; SKILL.md memuat tabel "What to read" yang memberi tahu agent file mana yang dibaca untuk tiap tugas.

## Skrip

```bash
python3 android-ui/scripts/lint_ui.py app/src/main
python3 android-ui/scripts/contrast.py "#5B5D58" "#F7F7F5"   # selalu beri tanda kutip
python3 android-ui/scripts/validate_tokens.py "#3B5BA9" --package com.example.app
python3 android-ui/scripts/scan.py app --format md --out security-report.md
python3 android-ui/scripts/scan.py app --fail-on high
```

- Suppress temuan scanner: `// sec-ignore: RULE_ID alasan` (alasan wajib, tanpa alasan diabaikan).
- Suppress aturan linter: `// ui-ignore: RULE_ID alasan`.
- `scan.py` keluar dengan kode 2 bila path salah atau tidak ada file sumber, jadi hasil kosong tidak pernah dianggap bersih.
- `validate_tokens.py --write` tidak menimpa `Color.kt`/`Theme.kt` yang sudah ada kecuali dengan `--force`.

## Tes

```bash
python3 install.py --validate
python3 tests/run_tests.py
```

## Batasan

- `scan.py` berbasis pola (tanpa data-flow); bisa false positive dan bisa meleset.
- `lint_ui.py` hanya menangkap pelanggaran terukur; kualitas visual tetap perlu review manusia.
- Hasil audit bukan jaminan aman dan bukan pengganti pentest atau review backend.
- Verifikasi rekomendasi API ke dokumentasi resmi untuk versi Android/AndroidX yang dipakai.
