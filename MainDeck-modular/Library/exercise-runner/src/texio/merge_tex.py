# src/texio/merge_tex.py
from pathlib import Path
import json

HEADER = r"% --- Auto-generated solutions file (no preamble) ---"

def merge_hierarchical(ex_json: str, solutions_dir: str, out_path: str):
    data = json.loads(Path(ex_json).read_text(encoding="utf-8"))
    sdir = Path(solutions_dir)
    out = Path(out_path)

    parts = [HEADER, ""]
    for main in data["tasks"]:
        tid = main["task_id"]
        context = (main.get("body_tex") or "").strip()
        subtasks = main.get("subtasks", [])

        # Section: Aufgabe X
        parts.append(f"\\section*{{Aufgabe {tid}}}")
        if context:
            parts.append(context)
            parts.append("")

        if subtasks:
            for sub in subtasks:
                sid = sub["sub_id"]          # "1.1"
                parts.append(f"\\subsection*{{({sid})}}")
                sol_file = sdir / f"{sid}.tex"
                if sol_file.exists():
                    parts.append(sol_file.read_text(encoding="utf-8").strip())
                else:
                    parts.append(r"\textit{(Noch keine Lösung generiert.)}")
                parts.append("")
        else:
            # Lösung zu Hauptaufgabe (falls ohne Subtasks)
            sol_file = sdir / f"{tid}.tex"
            if sol_file.exists():
                parts.append(sol_file.read_text(encoding="utf-8").strip())
                parts.append("")
            else:
                parts.append(r"\textit{(Noch keine Lösung generiert.)}")
                parts.append("")

    out.write_text("\n".join(parts), encoding="utf-8")
