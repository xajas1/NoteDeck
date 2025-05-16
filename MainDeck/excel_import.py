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
#   Mapping Content‑Typ  →  LaTeX‑Umgebung & \subsection{}‑Label            #
# --------------------------------------------------------------------------- #
ENVIRONMENTS = {
    "DEF":  "DEF",
    "CONC": "CONC",
    "EXA":  "EXA",
    "PROP": "PROP",
    "KORO": "KORO",
    "LEM":  "LEM",
    "THEO": "THEO",
    "REM":  "REM",
    "STUD": "STUD",
    "PRF":  "PRF",
}

CTYP_LABELS = {
    "DEF":  "Definition",
    "CONC": "Concept",
    "EXA":  "Example",
    "PROP": "Proposition",
    "KORO": "Corollar",
    "LEM":  "Lemma",
    "THEO": "Theorem",
    "REM":  "Remark",
    "STUD": "Study",
    "PRF":  "Proof",
}

SUBSECTION_ORDER = [
    "Definition",
    "Concept",
    "Example",
    "Proposition",
    "Corollar",
    "Lemma",
    "Theorem",
    "Remark",
    "Proof",
    "Study",
]

CTYP_ORDER = {label: i for i, label in enumerate(SUBSECTION_ORDER)}

# --------------------------------------------------------------------------- #
#   Hilfsfunktionen                                                           #
# --------------------------------------------------------------------------- #
def find_section_position(script_text: str, topic: str) -> int | None:
    pattern = re.compile(r"\\section\{([^}]*)\}", re.IGNORECASE)
    topic_normalized = topic.strip().lower()
    for match in pattern.finditer(script_text):
        section_title = match.group(1).strip().lower()
        if section_title == topic_normalized:
            return match.end()
    return None


def find_insertion_point(script_text: str, topic: str, ctyp: str) -> int | tuple[int, str] | None:
    section_start = find_section_position(script_text, topic)
    if section_start is None:
        return None

    label = CTYP_LABELS.get(ctyp, "")
    label_index = SUBSECTION_ORDER.index(label) if label in SUBSECTION_ORDER else -1

    sub_pat = re.compile(r"\\subsection\{([^}]*)\}")
    all_subs = list(sub_pat.finditer(script_text, section_start))

    # Suche passende Subsection
    for match in all_subs:
        if match.group(1) == label:
            sub_start = match.end()
            next_head = next((m for m in all_subs if m.start() > sub_start), None)
            sub_end = next_head.start() if next_head else len(script_text)
            env_type = ENVIRONMENTS[ctyp]
            env_end_pat = re.compile(rf"\\end\{{{re.escape(env_type)}\}}")
            matches = [m for m in env_end_pat.finditer(script_text, sub_start, sub_end)]
            insert_pos = matches[-1].end() if matches else sub_end
            return insert_pos, script_text  # Rückgabe auch ohne Änderung

    # Subsection nicht vorhanden → neue einfügen
    insertion_point = section_start
    for match in all_subs:
        existing_label = match.group(1)
        if existing_label in SUBSECTION_ORDER:
            existing_index = SUBSECTION_ORDER.index(existing_label)
            if existing_index > label_index:
                insertion_point = match.start()
                break
            insertion_point = match.end()

        # Prüfe, ob andere Subsections existieren → finde die passende Stelle nach Ordnungsindex
    # Setze neuen Subsection-Block VOR die erste, die weiter hinten kommt
    for match in all_subs:
        existing_label = match.group(1)
        if existing_label in SUBSECTION_ORDER:
            existing_index = SUBSECTION_ORDER.index(existing_label)
            if existing_index > label_index:
                insertion_point = match.start()
                break
    # Falls keine spätere Subsection gefunden: ganz ans Ende der Section
    else:
        insertion_point = section_start
        for match in reversed(all_subs):
            if match.group(1) in SUBSECTION_ORDER:
                insertion_point = match.end()
                break


    new_sub = f"\n\n\\subsection{{{label}}}\n\n"
    updated_text = script_text[:insertion_point] + new_sub + script_text[insertion_point:]
    return insertion_point + len(new_sub), updated_text




def unit_exists(script_text: str, unit_id: str) -> bool:
    return re.search(rf"\{{{re.escape(str(unit_id))}\}}", script_text) is not None

def generate_environment(env_type: str, unit_id: str, description: str) -> str:
    return (
        f"\n\n"
        f"\\begin{{{env_type}}}{{{unit_id}}}{{{description}}}\n\n"
        f"\\end{{{env_type}}}\n\n"
    )

# --------------------------------------------------------------------------- #
#   Excel einlesen (mit stabiler Topic-Sortierung)                            #
# --------------------------------------------------------------------------- #
df = (
    pd.read_excel(EXCEL_PATH, sheet_name=MODULESHEET, header=HEADER_ROW)
    .loc[:, ["Subject", "UnitID", "Content", "CTyp", "Topic"]]
    .dropna()
)

# Zusatzspalte zur stabilen Sortierung
df["CTypSort"] = df["CTyp"].map(lambda c: CTYP_ORDER.get(CTYP_LABELS.get(c, ""), 99))

# Extrahiere Topic-Index aus UnitID (z. B. "HA-1-01-4" → 1)
df["TopicIndex"] = (
    df["UnitID"]
    .str.extract(r"[A-Z]+-\d+-(\d+)-")[0]
    .fillna("999")  # sehr hohe Zahl → landet ganz hinten
    .astype(int)
)


# Sortiere stabil nach Subject → TopicIndex → CTypSort → UnitID
df = df.sort_values(by=["Subject", "TopicIndex", "CTypSort", "UnitID"]).drop(columns=["TopicIndex"])


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
        script_paths[subj_name.lower()] = tex_path

if not script_paths:
    print("❌  Keine *_script.tex‑Dateien in MainDeck gefunden.")
    exit(1)

# --------------------------------------------------------------------------- #
#   Verarbeitung                                                              #
# --------------------------------------------------------------------------- #
for _, row in df.iterrows():
    subject = str(row["Subject"])
    unit_id = str(row["UnitID"])
    content = str(row["Content"])
    ctyp    = str(row["CTyp"])
    topic   = str(row["Topic"])

    if ctyp not in ENVIRONMENTS:
        continue

    script_path = script_paths.get(subject.lower())
    if script_path is None:
        print(f"⚠️  Kein Skript für Subject '{subject}' gefunden – Eintrag {unit_id} übersprungen.")
        continue

    with open(script_path, "r", encoding="utf-8") as fh:
        script_text = fh.read()

    if unit_exists(script_text, unit_id):
        continue

    result = find_insertion_point(script_text, topic, ctyp)
    if not result:
        print(f"❌  Keine passende Section für Topic '{topic}' in {script_path}")
        continue

    insert_pos, script_text = result



    env_code = generate_environment(ENVIRONMENTS[ctyp], unit_id, content)
    new_text = script_text[:insert_pos] + env_code + script_text[insert_pos:]

    with open(script_path, "w", encoding="utf-8") as fh:
        fh.write(new_text)

    print(f"✅ Eingefügt: {unit_id} → {script_path.name} unter Topic '{topic}' und Typ '{ctyp}'")

print("\n🎉  Alle Subjects verarbeitet.")
