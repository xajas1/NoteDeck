from pathlib import Path
import pandas as pd
import re

# --------------------------------------------------------------------------- #
#   Konfiguration                                                             #
# --------------------------------------------------------------------------- #
BASE        = Path(".")
EXCEL_PATH  = BASE / "../Stud-Monitoring-neu.xlsm"
MODULESHEET = "CONTENT"
HEADER_ROW  = 3                          # Zeile 4 = Header (0‑basiert)

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
    """
    Liefert die Position, an der der neue Environment‑Block eingefügt werden soll:
    1.   \section{<Topic>} suchen                                 → section_start
    2.   \subsection{<Label>} innerhalb dieser Section suchen     → subsection_start
    3a.  Falls bereits ENV‑Blöcke vorhanden, hinter dem **letzten** \end{ENV} einfügen
    3b.  Sonst direkt hinter der Subsection‑Überschrift einfügen.
    """
    # 1) Section finden
    sec_pat  = re.compile(r"\\section\{([^}]*)\}")
    sec_iter = [(m.group(1), m.end()) for m in sec_pat.finditer(script_text)]

    section_start = None
    for title, end_pos in sec_iter:
        if topic.lower() in title.lower():
            section_start = end_pos
            break
    if section_start is None:
        return None

    # 2) passende Subsection (Label) innerhalb der Section finden
    label            = CTYP_LABELS.get(ctyp, "")
    sub_pat          = re.compile(rf"\\subsection\{{{re.escape(label)}\}}")
    sub_match        = sub_pat.search(script_text, section_start)
    subsection_start = sub_match.end() if sub_match else section_start  # Fallback

    # Grenze nach unten: nächster Section‑ oder Subsection‑Header
    next_header_pat = re.compile(r"(\\section\{|\\subsection\{)")
    next_header     = next_header_pat.search(script_text, subsection_start)
    subsection_end  = next_header.start() if next_header else len(script_text)

    # 3) Letztes vorhandenes \end{ENV} im Bereich suchen
    env_type       = ENVIRONMENTS[ctyp]
    env_end_pat    = re.compile(rf"\\end\{{{re.escape(env_type)}\}}")
    last_env_match = None
    for m in env_end_pat.finditer(script_text, subsection_start, subsection_end):
        last_env_match = m
    if last_env_match:
        return last_env_match.end()     # hinter letztem vorhandenen ENV
    return subsection_start              # sonst direkt nach der Überschrift


def unit_exists(script_text: str, unit_id: str) -> bool:
    """True, wenn die UnitID bereits irgendwo im Skript vorkommt."""
    return re.search(rf"\{{{re.escape(unit_id)}\}}", script_text) is not None


def generate_environment(env_type: str, unit_id: str, description: str) -> str:
    """LaTeX‑Block für eine Content‑Unit erzeugen."""
    return (
        f"\n\\begin{{{env_type}}}{{{unit_id}}}{{{description}}}\n\n"
        f"\\end{{{env_type}}}\n"
    )

# --------------------------------------------------------------------------- #
#   Daten laden                                                               #
# --------------------------------------------------------------------------- #
df = (
    pd.read_excel(EXCEL_PATH, sheet_name=MODULESHEET, header=HEADER_ROW)
      .loc[:, ["Subject", "UnitID", "Content", "CTyp", "Topic"]]
      .dropna()
)

# --------------------------------------------------------------------------- #
#   Verarbeitung                                                              #
# --------------------------------------------------------------------------- #
for _, row in df.iterrows():
    subject, unit_id, content, ctyp, topic = row

    # --- Vor‑Filtern -------------------------------------------------------- #
    if not all([subject, unit_id, content, ctyp, topic]):
        continue
    if ctyp not in ENVIRONMENTS or subject != "EFT1":
        continue

    env_type   = ENVIRONMENTS[ctyp]
    script_path = BASE / subject / f"{subject}_script.tex"
    if not script_path.exists():
        print(f"⚠️  Datei nicht gefunden: {script_path}")
        continue

    with open(script_path, "r", encoding="utf-8") as fh:
        script = fh.read()

    if unit_exists(script, unit_id):
        # Schon vorhanden → als „generiert“ anerkannt, nichts tun
        continue

    # Einfüge‑Position bestimmen
    insert_pos = find_insertion_point(script, topic, ctyp)
    if insert_pos is None:
        print(f"❌ Kein passender Abschnitt für Topic '{topic}' in {script_path}")
        continue

    # Einfügen & Datei schreiben
    env_code  = generate_environment(env_type, unit_id, content)
    new_script = script[:insert_pos] + env_code + script[insert_pos:]
    with open(script_path, "w", encoding="utf-8") as fh:
        fh.write(new_script)

    print(f"✅ Eingefügt: {unit_id} in {script_path}")
