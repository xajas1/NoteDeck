import json
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# === FastAPI Setup ===
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Konfiguration ===
ROOT = Path(__file__).resolve().parent.parent  # MainDeck-modular
MODULE_DIR = ROOT / "Library" / "Module"
SCRIPT_DIR = ROOT / "Library" / "Scripts"
STRUCTURE_BASE = Path(__file__).resolve().parent  # Programme/
PROJECT_FILE = STRUCTURE_BASE / "local_projects.json"

# === LaTeX Header (gekürzt) ===
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

class ExportRequest(BaseModel):
    project: str

@app.post("/export-tex")
def export_tex(req: ExportRequest):
    structure = load_structure(req.project)
    if not structure:
        return {"success": False, "message": f"Projektstruktur '{req.project}' nicht gefunden."}
    path = write_tex(req.project, structure)
    return {"success": True, "message": f"Export abgeschlossen: {path.relative_to(ROOT)}"}

def load_structure(project_name):
    if not PROJECT_FILE.exists():
        raise FileNotFoundError("local_projects.json nicht gefunden")
    with open(PROJECT_FILE, encoding="utf8") as f:
        local_data = json.load(f)
        projects = local_data.get("projects", {})
        if project_name not in projects:
            raise ValueError(f"Projekt '{project_name}' nicht gefunden")
        return projects[project_name]["structure"]

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
    return output_path

if __name__ == "__main__":
    uvicorn.run("tex_exporter:app", host="127.0.0.1", port=8050, reload=True)
