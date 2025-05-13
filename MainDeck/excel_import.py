import pandas as pd
from pathlib import Path
import re

# === EINSTELLUNGEN =========================
EXCEL_PATH = Path("Stud-Monitoring-neu.xlsm")  # oder absoluter Pfad
SCRIPT_DIR = Path("MainDeck")
MODULESHEET = "CONTENT"
HEADER_ROW = 3  # 0-basiert, also: "Zeile 4" = 3

# === LADE DATEN AUS EXCEL ===================
df = pd.read_excel(EXCEL_PATH, sheet_name=MODULESHEET, header=HEADER_ROW)
df = df[["UnitID", "Content", "CTyp"]].dropna()

# === GRUPPIERE NACH SUBJECT ==============

for _, row in df.iterrows():
    unitid = row["UnitID"]
    content = row["Content"]
    ctyp = row["CTyp"]

    try:
        subject, _, topic, unit = unitid.split("-")
    except ValueError:
        print(f"❌ Ungültige UnitID: {unitid}")
        continue

    tex_file = SCRIPT_DIR / subject / f"{subject}_script.tex"
    if not tex_file.exists():
        print(f"⚠️  Datei nicht gefunden: {tex_file}")
        continue

    # Latex-Datei lesen
    with open(tex_file, "r", encoding="utf-8") as f:
        tex_content = f.read()

    # Prüfe, ob Unit schon existiert
    label = f"{subject}.{topic}.{unit}"
    pattern = re.compile(rf"\\begin\{{{ctyp}\}}\{{{re.escape(label)}\}}")
    if pattern.search(tex_content):
        continue  # bereits vorhanden

    # Finde passende Section (z. B. \section{4 ...} oder \section{Homologiegruppe})
    section_pattern = re.compile(r"\\section\{(.+?)\}")
    insert_pos = None

    for match in section_pattern.finditer(tex_content):
        title = match.group(1).strip()
        if title.startswith(topic) or topic in title:
            insert_pos = tex_content.find("\n", match.end()) + 1
            break

    if insert_pos is None:
        print(f"⚠️  Keine passende Section für Topic {topic} in {tex_file.name}")
        continue

    # Neue Umgebung generieren
    env_block = (
        f"\n\\begin{{{ctyp}}}{{{label}}}{{{content}}}\n"
        f"% TODO: Inhalt ergänzen\n"
        f"\\end{{{ctyp}}}\n"
    )

    # Block einfügen und speichern
    new_content = tex_content[:insert_pos] + env_block + tex_content[insert_pos:]
    with open(tex_file, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"✅ Eingefügt: {label} in {tex_file.name}")
