# src/llm/solve.py
import json
from pathlib import Path
from src.llm.client import get_client, get_model

SOLVER_SYS = (
    "Du bist ein präziser wissenschaftlicher Assistent. "
    "Antworte ausschließlich mit LaTeX-Text (kein Markdown, keine Sternchen, "
    "keine Fettschrift, keine Aufzählungen oder nummerierten Listen). "
    "Keine Aufzählungen mit 1., 2., - oder *.\n"
    "Nur Fließtext mit mathematischen Umgebungen (align, equation, etc.), "
    "aber keine Textlisten.\n"
    "Verwende vollständige Sätze, klare Argumentationsschritte und korrekte Notation.\n"
    "Erzeuge ausschließlich den TeX-Body (keine Präambel, kein \\begin{document}).\n"
    "Nummeriere Gleichungen nur, wenn sie im Text referenziert werden."
)


def _solve_prompt(task_id: str, body_tex: str) -> str:
    return (
        f"Unteraufgabe: {task_id}\n"
        f"Aufgabentext (TeX):\n{body_tex}\n\n"
        "Anforderungen:\n"
        "- Nur Lösungstext als TeX-Body ausgeben (keine Präambel).\n"
        "- Korrekt, knapp, nachvollziehbar.\n"
    )

def solve_sheet(ex_json: str, out_dir: str):
    client = get_client()
    model = get_model("solve", "o4-mini")
    data = json.loads(Path(ex_json).read_text(encoding="utf-8"))

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    for main in data["tasks"]:
        # Hauptaufgabe (Kontext) hat i.d.R. keine direkte Lösung—wir lösen die Subtasks.
        subtasks = main.get("subtasks", [])
        if subtasks:
            for sub in subtasks:
                sid = sub["sub_id"]             # z.B. "1.1"
                body = sub["body_tex"]
                resp = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": SOLVER_SYS},
                        {"role": "user", "content": _solve_prompt(sid, body)}
                    ],
                    temperature=0.2
                )
                tex = resp.choices[0].message.content.strip()
                (out / f"{sid}.tex").write_text(tex, encoding="utf-8")
        else:
            # Falls es ausnahmsweise eine Hauptaufgabe ohne Subtasks gibt, lösen wir sie direkt.
            tid = main["task_id"]               # z.B. "1"
            body = main.get("body_tex", "")
            if body.strip():
                resp = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": SOLVER_SYS},
                        {"role": "user", "content": _solve_prompt(tid, body)}
                    ],
                    temperature=0.2
                )
                tex = resp.choices[0].message.content.strip()
                (out / f"{tid}.tex").write_text(tex, encoding="utf-8")

if __name__ == "__main__":
    import sys
    solve_sheet(sys.argv[1], sys.argv[2])
