# src/build_tex.py
import json, sys
from pathlib import Path

PREAMBLE = r"""\documentclass[11pt,a4paper]{article}
\usepackage[margin=2.5cm]{geometry}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{lmodern}
\usepackage{amsmath,amssymb,amsthm,mathtools,physics,bm}
\usepackage{microtype}
\title{Lösungen}
\date{}
\begin{document}
\maketitle
"""

POSTAMBLE = r"\end{document}\n"

def build_full_tex(ex_json_path: str, version: str, out_path: str | None = None, title: str | None = None):
    ex_json = Path(ex_json_path)
    run_dir = ex_json.parent                 # .../build
    sol_dir = run_dir / "solutions" / version  # .../build/solutions/vX
    if not sol_dir.exists():
        raise SystemExit(f"[!] Solutions-Verzeichnis nicht gefunden: {sol_dir}")

    data = json.loads(ex_json.read_text(encoding="utf-8"))

    preamble = PREAMBLE if not title else PREAMBLE.replace(r"\title{Lösungen}", fr"\title{{{title}}}")
    parts = [preamble]

    for main in data.get("tasks", []):
        tid = main["task_id"]                      # "1"
        context = (main.get("body_tex") or "").strip()
        subtasks = main.get("subtasks", [])

        # Abschnitt: Aufgabe 1
        parts.append(fr"\section*{{Aufgabe {tid} [{version}]}}")

        # --- Hauptaufgabenstellung (Kontext/Setting), falls vorhanden
        if context:
            parts.append(r"\paragraph{Aufgabentext.}")
            parts.append(context)
            parts.append("")

        if subtasks:
            # Für jede Unteraufgabe: erst Aufgabenstellung, dann Lösung
            for sub in subtasks:
                sid = sub["sub_id"]               # "1.1"
                sbody = (sub.get("body_tex") or "").strip()

                parts.append(fr"\subsection*{{({sid}) [{version}]}}")

                # Aufgabenstellung der Unteraufgabe
                parts.append(r"\paragraph{Aufgabentext.}")
                parts.append(sbody if sbody else r"\textit{(Kein Aufgabentext gefunden.)}")
                parts.append("")

                # Lösung der Unteraufgabe
                parts.append(r"\paragraph{Lösung.}")
                sol_file = sol_dir / f"{sid}.tex"
                parts.append(sol_file.read_text(encoding="utf-8").strip()
                             if sol_file.exists()
                             else r"\textit{(Keine Lösung in dieser Version vorhanden.)}")
                parts.append("")
        else:
            # Hauptaufgabe ohne Unteraufgaben: auch hier Aufgabe → Lösung
            parts.append(r"\paragraph{Lösung.}")
            sol_file = sol_dir / f"{tid}.tex"
            parts.append(sol_file.read_text(encoding="utf-8").strip()
                         if sol_file.exists()
                         else r"\textit{(Keine Lösung in dieser Version vorhanden.)}")
            parts.append("")

    parts.append(POSTAMBLE)
    out_path = (run_dir / f"solutions_{version}_full.tex") if out_path is None else Path(out_path)
    out_path.write_text("\n".join(parts), encoding="utf-8")
    print(f"✔ gebaut → {out_path}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage:")
        print("  python -m src.build_tex /path/to/exercises.json v1 [optional_out.tex] [optional_title...]")
        raise SystemExit(1)
    ex_json = sys.argv[1]
    version = sys.argv[2]
    out = sys.argv[3] if len(sys.argv) >= 4 else None
    title = " ".join(sys.argv[4:]) if len(sys.argv) >= 5 else None
    build_full_tex(ex_json, version, out, title)
