import json
from pathlib import Path
import argparse

# === Konfiguration ===
ROOT = Path(__file__).resolve().parent.parent  # MainDeck-modular
MODULE_DIR = ROOT / "Library" / "Module"
SCRIPT_DIR = ROOT / "Library" / "Scripts"
STRUCTURE_BASE = Path(__file__).resolve().parent  # Programme/

# === LaTeX Header (gekürzt für Demo-Zwecke) ===
LATEX_HEADER = r"""
\documentclass[10pt, letterpaper]{article}
\usepackage[margin=3cm]{geometry}
\usepackage[utf8]{inputenc}
\usepackage{amsmath,amssymb,amsthm}
\begin{document}
\tableofcontents
\newpage
"""

LATEX_FOOTER = r"""
\end{document}
"""

def load_structure(project_name):
    json_path = STRUCTURE_BASE / f"export_structure_{project_name}.json"
    if not json_path.exists():
        raise FileNotFoundError(f"Strukturdatei nicht gefunden: {json_path}")
    with open(json_path, encoding="utf8") as f:
        return json.load(f)

def read_unit_tex(unit_id):
    tex_path = MODULE_DIR / f"{unit_id}.tex"
    if not tex_path.exists():
        return f"% --- Fehlend: {unit_id} ---\n% Datei nicht gefunden\n"
    with open(tex_path, encoding="utf8") as f:
        content = f.read().strip()
        if not content:
            return f"% --- Leer: {unit_id} ---\n% Inhalt fehlt\n"
        return f"% --- START: {unit_id} ---\n{content}\n% --- END: {unit_id} ---"

def generate_body(structure):
    tex_lines = []
    for section in structure:
        tex_lines.append(f"\\section{{{section['name']}}}")
        for sub in section.get("subsections", []):
            tex_lines.append(f"\\subsection{{{sub['name']}}}")
            for uid in sub.get("unitIDs", []):
                tex_lines.append(read_unit_tex(uid))
    return "\n\n".join(tex_lines)

def write_tex(project_name, structure):
    SCRIPT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = SCRIPT_DIR / f"{project_name}.tex"
    body = generate_body(structure)
    with open(output_path, "w", encoding="utf8") as f:
        f.write(LATEX_HEADER)
        f.write("\n\n")
        f.write(body)
        f.write("\n\n")
        f.write(LATEX_FOOTER)
    print(f"✅ Export abgeschlossen: {output_path.relative_to(ROOT)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True, help="Projektname (z.B. test_project4)")
    args = parser.parse_args()

    structure = load_structure(args.project)
    write_tex(args.project, structure)
