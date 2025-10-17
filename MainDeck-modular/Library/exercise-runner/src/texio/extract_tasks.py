# src/texio/extract_tasks.py
import re, json
from pathlib import Path
from typing import Dict, List

MARKER_RX = re.compile(r"\[\[([0-9A-Za-z\.\-]+)\]\]")

def extract_hierarchical(tex_path: str, out_json: str):
    text = Path(tex_path).read_text(encoding="utf-8")
    matches = list(MARKER_RX.finditer(text))

    # Speicherstruktur
    tasks: Dict[str, dict] = {}
    order: List[str] = []  # Reihenfolge der Hauptaufgaben

    # Hilfsfunktion: Textsegment zwischen Marker i und i+1
    def segment(i: int) -> str:
        start = matches[i].end()
        end = matches[i+1].start() if i+1 < len(matches) else len(text)
        return text[start:end].strip()

    for i, m in enumerate(matches):
        ident = m.group(1)             # z.B. "1", "1.1", "2", ...
        parts = ident.split(".")

        # Hauptaufgabe
        if len(parts) == 1:
            tid = parts[0]
            body = segment(i)
            if tid not in tasks:
                tasks[tid] = {"task_id": tid, "body_tex": body, "subtasks": []}
                order.append(tid)
            else:
                # falls zuvor Subtasks ohne Hauptmarker auftauchten
                tasks[tid]["body_tex"] = body

        # Unteraufgabe (genau eine Ebene tiefer: "X.Y")
        elif len(parts) == 2:
            parent = parts[0]           # "1" aus "1.1"
            sub_id = ident              # "1.1"
            body = segment(i)
            if parent not in tasks:
                # Parent noch nicht definiert? Stub anlegen.
                tasks[parent] = {"task_id": parent, "body_tex": "", "subtasks": []}
                order.append(parent)
            tasks[parent]["subtasks"].append({"sub_id": sub_id, "body_tex": body})

        else:
            # Optional: tieferes Nesting behandeln (1.1.a etc.) → hier warnend als Flachtext ablegen
            parent = parts[0]
            sub_id = ident
            body = segment(i)
            if parent not in tasks:
                tasks[parent] = {"task_id": parent, "body_tex": "", "subtasks": []}
                order.append(parent)
            tasks[parent]["subtasks"].append({"sub_id": sub_id, "body_tex": body})

    # Reihenfolge der Hauptaufgaben respektieren
    out = {"tasks": [tasks[k] for k in order]}
    Path(out_json).write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"✔ extracted {sum(1+len(t['subtasks']) for t in out['tasks'])} items "
          f"({len(out['tasks'])} main tasks) → {out_json}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python -m src.texio.extract_tasks INPUT.tex OUTPUT.json")
        raise SystemExit(1)
    extract_hierarchical(sys.argv[1], sys.argv[2])
