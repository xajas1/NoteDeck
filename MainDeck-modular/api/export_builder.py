import sys
import json
from pathlib import Path
from glob import glob

def build_tex_file(project_name: str):
    # Absoluter Einstiegspunkt: MainDeck-modular/
    base_dir = Path(__file__).resolve().parents[1]
    export_path = base_dir / "Export" / f"{project_name}.json"
    modules_path = base_dir / "Library" / "Module"       # ← angepasst!
    scripts_dir = base_dir / "Library" / "Scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)

    # Suche vorhandene Dateien wie Test.tex, Test_v1.tex, Test_v2.tex, ...
    existing_versions = glob(str(scripts_dir / f"{project_name}*.tex"))
    version = 1
    while (scripts_dir / f"{project_name}_v{version}.tex").exists():
        version += 1

    output_path = scripts_dir / f"{project_name}_v{version}.tex"
    header_path = base_dir / "Library" / "Scripts" / "header.tex"

    if not export_path.exists():
        raise FileNotFoundError(f"❌ JSON-Struktur nicht gefunden: {export_path}")
    if not header_path.exists():
        raise FileNotFoundError(f"❌ Header-Datei fehlt: {header_path}")

    with open(export_path, "r", encoding="utf-8") as f:
        project_data = json.load(f)

    with open(header_path, "r", encoding="utf-8") as f:
        header = f.read()

    body_lines = []

    for section in project_data["structure"]:
        body_lines.append(f"\\section{{{section['name']}}}\n")
        for sub in section["subsections"]:
            body_lines.append(f"\\subsection{{{sub['name']}}}\n")
            for uid in sub["unitIDs"]:
                unit_file = modules_path / f"{uid}.tex"
                if unit_file.exists():
                    content = unit_file.read_text(encoding="utf-8").strip()
                    body_lines.append(content + "\n")
                else:
                    body_lines.append(f"% ⚠️ FEHLT: {uid}.tex\n")

    content = header.replace("……CONTENT", "\n".join(body_lines).strip())

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

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
