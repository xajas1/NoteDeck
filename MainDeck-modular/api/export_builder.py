import sys
import json
from pathlib import Path
from glob import glob

def build_tex_file(project_name: str):
    # Hauptverzeichnis
    base_dir = Path(__file__).resolve().parents[1]

    export_path   = base_dir / "Export" / f"{project_name}.json"
    lib_path      = base_dir / "Library" / "Library.json"
    scripts_base  = base_dir / "Library" / "Scripts"
    project_dir   = scripts_base / project_name
    header_path   = scripts_base / "header.tex"

    # Erstelle Zielordner für dieses Projekt
    project_dir.mkdir(parents=True, exist_ok=True)

    # Finde vorhandene Tex-Versionen in diesem Projektordner
    existing_versions = glob(str(project_dir / f"{project_name}_v*.tex"))
    version = 1
    while (project_dir / f"{project_name}_v{version}.tex").exists():
        version += 1

    output_path = project_dir / f"{project_name}_v{version}.tex"

    if not export_path.exists():
        raise FileNotFoundError(f"❌ JSON-Struktur nicht gefunden: {export_path}")
    if not header_path.exists():
        raise FileNotFoundError(f"❌ Header-Datei fehlt: {header_path}")
    if not lib_path.exists():
        raise FileNotFoundError(f"❌ Library.json fehlt: {lib_path}")

    # Lade Daten
    with open(export_path, "r", encoding="utf-8") as f:
        project_data = json.load(f)
    with open(lib_path, "r", encoding="utf-8") as f:
        lib_data = json.load(f)
    with open(header_path, "r", encoding="utf-8") as f:
        header = f.read()

    # Erstelle Dictionary für schnellen Zugriff auf Body per UID
    unit_dict = {entry["UID"]: entry for entry in lib_data}

    # Füge Inhalte zusammen
    body_lines = []
    for section in project_data["structure"]:
        body_lines.append(f"\\section{{{section['name']}}}\n")
        for sub in section["subsections"]:
            body_lines.append(f"\\subsection{{{sub['name']}}}\n")
            for uid in sub["unitUIDs"]:
                entry = unit_dict.get(uid)
                if entry:
                    unit_id = entry.get("UnitID", uid)
                    env = entry.get("CTyp", "unit")
                    title = entry.get("Content", "Ohne Titel")
                    body  = entry.get("Body", "").strip() or "% TODO: Inhalt ergänzen (Tex)"
                    block = f"\\begin{{{env}}}{{{unit_id}}}{{{title}}}\n{body}\n\\end{{{env}}}"
                    body_lines.append(block + "\n")
                else:
                    body_lines.append(f"% ⚠️ FEHLT in Library.json: {uid}\n")

    tex_content = header.replace("……CONTENT", "\n".join(body_lines).strip())

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(tex_content)

    print(f"✅ Export abgeschlossen: {output_path.relative_to(base_dir)}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("⚠️ Bitte Projektnamen angeben: python export_builder.py EFT1")
        sys.exit(1)

    try:
        build_tex_file(sys.argv[1])
    except Exception as e:
        print("❌ Fehler:", e)
        sys.exit(1)
