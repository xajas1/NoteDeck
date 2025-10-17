from pathlib import Path
import pandas as pd
import re

# --------------------------------------------------------------------------- #
#   Projektverzeichnisse                                                      #
# --------------------------------------------------------------------------- #
SCRIPT_ROOT   = Path(__file__).resolve().parent
PROJECT_ROOT  = SCRIPT_ROOT.parent
EXCEL_PATH    = PROJECT_ROOT / "Stud-Monitoring-neu.xlsm"

MODULESHEET   = "CONTENT"
HEADER_ROW    = 3

# --------------------------------------------------------------------------- #
#   Mapping Content‑Typ  →  LaTeX‑Umgebung & Überschriftlabel                #
# --------------------------------------------------------------------------- #
ENVIRONMENTS = {
    "DEF":  "DEF",
    "PROP": "PROP",
    "THEO": "THEO",
    "LEM":  "LEM",
    "KORO": "KORO",
    "REM":  "REM",
    "EXA":  "EXA",
    "STUD": "STUD",
    "CONC": "CONC",
}

CTYP_LABELS = {
    "DEF":  "Definition",
    "PROP": "Proposition",
    "THEO": "Theorem",
    "LEM":  "Lemma",
    "KORO": "Corollar",
    "REM":  "Remark",
    "EXA":  "Example",
    "STUD": "Study",
    "CONC": "Concept",
}

# --------------------------------------------------------------------------- #
#   Hilfsfunktionen                                                           #
# --------------------------------------------------------------------------- #
def find_insertion_point(script_text: str, topic: str, ctyp: str) -> int | None:
    sec_pat = re.compile(r"\\section\{([^}]*)\}")
    section_start = next(
        (m.end() for m in sec_pat.finditer(script_text)
         if topic.lower() in m.group(1).lower()),
        None
    )
    if section_start is None:
        return None

    label = CTYP_LABELS.get(ctyp, "")
    sub_pat = re.compile(rf"\\subsection\{{{re.escape(label)}\}}")
    sub_match = sub_pat.search(script_text, section_start)
    sub_start = sub_match.end() if sub_match else section_start

    next_head = re.search(r"(\\section\{|\\subsection\{)", script_text[sub_start:])
    sub_end = sub_start + next_head.start() if next_head else len(script_text)

    env_type = ENVIRONMENTS[ctyp]
    env_end_pat = re.compile(rf"\\end\{{{re.escape(env_type)}\}}")
    last_env = [m for m in env_end_pat.finditer(script_text, sub_start, sub_end)]
    return last_env[-1].end() if last_env else sub_start

def unit_exists(script_text: str, unit_id: str) -> bool:
    return re.search(rf"\{{{re.escape(str(unit_id))}\}}", script_text) is not None

def generate_environment(env_type: str, unit_id: str, description: str) -> str:
    """Erzeugt einen Block mit garantierter Leerzeile davor und danach."""
    return (
        f"\n\n"
        f"\\begin{{{env_type}}}{{{unit_id}}}{{{description}}}\n\n"
        f"\\end{{{env_type}}}\n\n"
    )

# --------------------------------------------------------------------------- #
#   Excel einlesen                                                            #
# --------------------------------------------------------------------------- #
df = (
    pd.read_excel(EXCEL_PATH, sheet_name=MODULESHEET, header=HEADER_ROW)
    .loc[:, ["Subject", "UnitID", "Content", "CTyp", "Topic"]]
    .dropna()
    .sort_values(["Subject", "UnitID"])
)

# --------------------------------------------------------------------------- #
#   Verfügbare Skriptdateien ermitteln                                        #
# --------------------------------------------------------------------------- #
script_paths = {}
for subj_dir in SCRIPT_ROOT.iterdir():
    if not subj_dir.is_dir():
        continue
    subj_name = subj_dir.name
    tex_path = subj_dir / f"{subj_name}_script.tex"
    if tex_path.exists():
        script_paths[subj_name] = tex_path

if not script_paths:
    print("❌  Keine *_script.tex‑Dateien in MainDeck gefunden.")
    exit(1)

# --------------------------------------------------------------------------- #
#   Verarbeitung                                                              #
# --------------------------------------------------------------------------- #
for _, row in df.iterrows():
    subject, unit_id, content, ctyp, topic = map(str, row)

    if ctyp not in ENVIRONMENTS:
        continue

    script_path = script_paths.get(subject)
    if script_path is None:
        print(f"⚠️  Kein Skript für Subject '{subject}' gefunden – Eintrag {unit_id} übersprungen.")
        continue

    with open(script_path, "r", encoding="utf-8") as fh:
        script_text = fh.read()

    if unit_exists(script_text, unit_id):
        continue

    insert_pos = find_insertion_point(script_text, topic, ctyp)
    if insert_pos is None:
        print(f"❌  Keine passende Section/Subsection für Topic '{topic}' in {script_path}")
        continue

    # Erzeuge Block mit garantierten Zeilenumbrüchen davor und danach
    env_code = generate_environment(ENVIRONMENTS[ctyp], unit_id, content)

    # Füge den Block direkt ein (keine Prüfung nötig)
    new_text = script_text[:insert_pos] + env_code + script_text[insert_pos:]

    with open(script_path, "w", encoding="utf-8") as fh:
        fh.write(new_text)

    print(f"✅ Eingefügt: {unit_id} → {script_path}")

print("\n🎉  Alle Subjects verarbeitet.")
