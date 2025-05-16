import pandas as pd
from pathlib import Path
import re

EXCEL_PATH = Path("../Stud-Monitoring-neu.xlsm")
MODULESHEET = "CONTENT"
HEADER_ROW = 3

SCRIPT_DIR = Path(".")
MODULE_DIR = Path("..") / "Module"

# Mapping Contenttype zu LaTeX-Umgebung
ENV_MAP = {
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


def parse_unit_id(unit_id):
    parts = unit_id.split("-")
    if len(parts) < 4:
        return None
    subj = parts[0]
    topic_name = parts[2]  # ACHTUNG: wird ignoriert, es zählt nur das Topic in Excel
    return subj


def unit_exists_in_script(script_text, unit_id):
    return unit_id in script_text


def insert_unit_into_script(script_text, topic, unit_id, content, env):
    pattern = r"(\\section\{"+re.escape(topic)+r"\})"
    match = re.search(pattern, script_text)
    if not match:
        print(f"❌ Kein Abschnitt '\\section{{{topic}}}' im Skript gefunden – Unit {unit_id} übersprungen")
        return script_text

    insert_pos = match.end()
    insertion = f"\n\n\\begin{{{env}}}{{{unit_id}}}{{{content}}}\n\n\\end{{{env}}}\n"

    return script_text[:insert_pos] + insertion + script_text[insert_pos:]


def main():
    df = pd.read_excel(EXCEL_PATH, sheet_name=MODULESHEET, header=HEADER_ROW)
    df = df[["Subject", "UnitID", "Content", "CTyp", "Topic"]].dropna()

    for index, row in df.iterrows():
        subject = row["Subject"]
        unit_id = row["UnitID"]
        content = row["Content"]
        ctyp = row["CTyp"]
        topic = row["Topic"]

        env = ENV_MAP.get(ctyp)
        if not env:
            print(f"⚠️  Kein Mapping für CTyp '{ctyp}' – Unit {unit_id} übersprungen")
            continue

        script_path = SCRIPT_DIR / subject / f"{subject}_script.tex"
        if not script_path.exists():
            print(f"⚠️  Datei nicht gefunden: {script_path}")
            continue

        with open(script_path, "r", encoding="utf-8") as f:
            script_text = f.read()

        if unit_exists_in_script(script_text, unit_id):
            continue  # Unit bereits vorhanden

        script_text_new = insert_unit_into_script(script_text, topic, unit_id, content, env)

        if script_text != script_text_new:
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(script_text_new)
            print(f"✅ Eingefügt: {unit_id} in {script_path}")
        else:
            print(f"❌ Überschrift für Topic '{topic}' nicht gefunden – Unit {unit_id} übersprungen")


if __name__ == "__main__":
    main()
