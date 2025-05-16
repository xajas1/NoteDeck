from pathlib import Path
import re
import sys

# ------------------------------------------------------------
# Konfiguration
SOURCE_DIR   = Path("Sources")
LIBRARY_FILE = Path("Library/Library.tex")

# ------------------------------------------------------------
# Lade Library.tex
if not LIBRARY_FILE.exists():
    sys.exit(f"❌  Datei {LIBRARY_FILE} nicht gefunden.")

lib_tex = LIBRARY_FILE.read_text(encoding="utf-8")

# ------------------------------------------------------------
# Pattern für Library-Umgebungen wie \begin{DEF}{A-1-03-02}{Titel} ... \end{DEF}
env_block_pattern = re.compile(
    r"\\begin\{(\w+)\}\{([A-Z]+-\d+-\d+-\d+)\}\{(.*?)\}(.*?)\\end\{\1\}",
    re.S,
)

env_blocks = {}
for match in env_block_pattern.finditer(lib_tex):
    env, uid, title, body = match.groups()
    env_blocks[uid] = (env, title, body, match)

print(f"📄 {len(env_blocks)} Einträge in Library.tex erkannt.")

# ------------------------------------------------------------
# Pattern für Source-Dateien: \begin{unit}{A-1-3-2} … \end{unit}
unit_block_pattern = re.compile(
    r"\\begin\{unit\}\{([A-Z]+-\d{1,2}-\d{1,2}-\d{1,2})\}(.*?)\\end\{unit\}",
    re.S,
)

# ------------------------------------------------------------
# Durchlaufe alle Source-Dateien
injected = 0
skipped  = 0
missing  = []

for file in SOURCE_DIR.glob("*.tex"):
    print(f"\n📁 Verarbeite: {file.name}")
    source = file.read_text(encoding="utf-8")

    for match in unit_block_pattern.finditer(source):
        short_uid, content = match.groups()
        print(f"🔎 Source-Fund: {short_uid}", end=" ")

        try:
            prefix, p, t, u = short_uid.split("-")
            full_uid = f"{prefix}-{int(p):01d}-{int(t):02d}-{int(u):02d}"
            print(f"→ {full_uid}")
        except ValueError:
            print(f"\n⚠️  Fehlerhafte UnitID: {short_uid}")
            continue

        if full_uid not in env_blocks:
            print(f"❌ Nicht gefunden in Library.tex")
            missing.append(full_uid)
            continue

        env, title, old_body, match_obj = env_blocks[full_uid]

        # Inhaltsschutz: nur ersetzen, wenn Platzhalter vorhanden
        if "% TODO: Inhalt ergänzen (Tex)" not in old_body.strip():
            print(f"⛔️ Bestehender Inhalt – wird nicht überschrieben.")
            skipped += 1
            continue

        start, end = match_obj.span()

        new_block = (
            f"\\begin{{{env}}}{{{full_uid}}}{{{title}}}\n"
            f"{content.strip()}\n"
            f"\\end{{{env}}}"
        )

        lib_tex = lib_tex[:start] + new_block + lib_tex[end:]
        injected += 1
        print(f"✅ Ersetzt.")

# ------------------------------------------------------------
# Library-Datei aktualisieren
if injected > 0:
    LIBRARY_FILE.write_text(lib_tex, encoding="utf-8")
    print(f"\n✅ {injected} Inhalt(e) erfolgreich in Library.tex eingefügt.")

if skipped > 0:
    print(f"\n⏭️  {skipped} Inhalt(e) wurden nicht überschrieben (nicht leer).")

if missing:
    print("\n⚠️ Für folgende UnitIDs wurde keine Umgebung in Library.tex gefunden:")
    for uid in sorted(set(missing)):
        print(f"   - {uid}")

if injected == 0 and not missing and skipped == 0:
    print("ℹ️  Keine Änderungen vorgenommen.")
