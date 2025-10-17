from pathlib import Path
import pandas as pd
import re

# --- Konfiguration ---
BASE = Path(".")
EXCEL_PATH = BASE / "../Stud-Monitoring-neu.xlsm"
SCRIPT_DIR = BASE / "EFT1"  # Nur EFT1 existiert bisher
MODULESHEET = "CONTENT"
HEADER_ROW = 3

ENVIRONMENTS = {
    "DEF": "DEF",
    "PROP": "PROP",
    "THEO": "THEO",
    "LEM": "LEM",
    "KORO": "KORO",
    "REM": "REM",
    "EXA": "EXA",
    "STUD": "STUD",
    "CONC": "CONC"
}

CTYP_LABELS = {
    "DEF": "Definition",
    "PROP": "Proposition",
    "THEO": "Theorem",
    "LEM": "Lemma",
    "KORO": "Corollar",
    "REM": "Remark",
    "EXA": "Example",
    "STUD": "Study",
    "CONC": "Concept"
}

# --- Hilfsfunktionen ---
def find_insertion_point(script_text, topic_str, content_type):
    # Suche nach \section{...} mit passendem Topic-Namen
    section_pattern = re.compile(r"\\section\{([^}]*)\}")
    section_positions = [(m.group(1), m.end()) for m in section_pattern.finditer(script_text)]
    
    topic_section_end = None
    for title, end_pos in section_positions:
        if topic_str.lower() in title.lower():
            topic_section_end = end_pos
            break

    if topic_section_end is None:
        return None

    # Suche nach \subsection{<Label>} innerhalb der Section
    label = CTYP_LABELS.get(content_type, "")
    subsection_pattern = re.compile(rf"\\subsection\{{{re.escape(label)}\}}")
    subsection_match = subsection_pattern.search(script_text, topic_section_end)

    if subsection_match:
        return subsection_match.end()

    # Fallback: direkt nach der Section einfügen
    return topic_section_end

def unit_exists(script_text, unit_id):
    return re.search(rf"\{{{re.escape(unit_id)}\}}", script_text) is not None

def generate_environment(env_type, unit_id, description):
    return f"""\n\\begin{{{env_type}}}{{{unit_id}}}{{{description}}}

\\end{{{env_type}}}\n"""

# --- Daten laden ---
df = pd.read_excel(EXCEL_PATH, sheet_name=MODULESHEET, header=HEADER_ROW)
df = df[["Subject", "UnitID", "Content", "CTyp", "Topic"]].dropna()

# --- Verarbeitung ---
for _, row in df.iterrows():
    subject, unit_id, content, ctyp, topic = row["Subject"], row["UnitID"], row["Content"], row["CTyp"], row["Topic"]

    if not all([subject, unit_id, content, ctyp, topic]):
        continue
    if ctyp not in ENVIRONMENTS:
        continue
    if subject != "EFT1":
        continue

    env_type = ENVIRONMENTS[ctyp]
    script_path = BASE / subject / f"{subject}_script.tex"

    if not script_path.exists():
        print(f"⚠️  Datei nicht gefunden: {script_path}")
        continue

    with open(script_path, "r", encoding="utf-8") as f:
        script = f.read()

    if unit_exists(script, unit_id):
        continue

    insert_point = find_insertion_point(script, topic, ctyp)
    if insert_point is None:
        print(f"❌ Kein passender Abschnitt für Topic: {topic} in {script_path}")
        continue

    env_code = generate_environment(env_type, unit_id, content)
    new_script = script[:insert_point] + env_code + script[insert_point:]

    with open(script_path, "w", encoding="utf-8") as f:
        f.write(new_script)

    print(f"✅ Eingefügt: {unit_id} in {script_path}")
