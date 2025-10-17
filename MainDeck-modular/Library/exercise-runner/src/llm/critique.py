# src/llm/critique.py
import json
from pathlib import Path
from src.llm.client import get_client, get_model

CRITIC_SYS = (
    "Du bist ein strenger wissenschaftlicher Korrektor.\n"
    "Bewerte Lösungen primär mathematisch: fehlende Gleichungen, lückenhafte Herleitungen, unklare Transformationsregeln.\n"
    "Antworte ausschließlich im JSON-Format mit folgenden Feldern:\n"
    "{"
    "\"score\": 0..1, "
    "\"verdict\": \"kurzes Urteil\", "
    "\"weaknesses\": [{\"code\": \"string\", \"msg\": \"kurz\", \"math_hint\": \"konkrete Formel/Schritt, der fehlt oder falsch ist\"}], "
    "\"fix_suggestions\": [\"konkrete mathematische Korrektur/Identität/Umformung als LaTeX\" ]"
    "}\n"
    "Keine Prosa außerhalb des JSON."
)



def critique_sheet(ex_json: str, solutions_dir: str, review_dir: str):
    """Bewertet jede (Unter-)Aufgabe aus der gegebenen Solutions-Version"""
    client = get_client()
    model = get_model("critic", "gpt-4o-mini")

    data = json.loads(Path(ex_json).read_text(encoding="utf-8"))
    sdir = Path(solutions_dir)
    rdir = Path(review_dir)
    rdir.mkdir(parents=True, exist_ok=True)

    sheet_summary = {"tasks": {}}

    for main in data["tasks"]:
        # prüfe alle Unteraufgaben
        subs = main.get("subtasks", [])
        if subs:
            for sub in subs:
                sid = sub["sub_id"]
                sol_path = sdir / f"{sid}.tex"
                if not sol_path.exists():
                    continue
                prompt = f"""Bewerte folgende Lösung (TeX) zur Unteraufgabe {sid}:

---BEGIN SOLUTION---
{sol_path.read_text(encoding="utf-8")}
---END SOLUTION---"""
                resp = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": CRITIC_SYS},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.0,
                    response_format={"type": "json_object"},
                )
                review = json.loads(resp.choices[0].message.content)
                Path(rdir / f"{sid}.json").write_text(
                    json.dumps(review, indent=2, ensure_ascii=False),
                    encoding="utf-8",
                )
                sheet_summary["tasks"][sid] = review
        else:
            # Hauptaufgabe ohne Unteraufgaben
            tid = main["task_id"]
            sol_path = sdir / f"{tid}.tex"
            if not sol_path.exists():
                continue
            prompt = f"""Bewerte folgende Lösung (TeX) zur Aufgabe {tid}:

---BEGIN SOLUTION---
{sol_path.read_text(encoding="utf-8")}
---END SOLUTION---"""
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": CRITIC_SYS},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.0,
                response_format={"type": "json_object"},
            )
            review = json.loads(resp.choices[0].message.content)
            Path(rdir / f"{tid}.json").write_text(
                json.dumps(review, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            sheet_summary["tasks"][tid] = review

    Path(rdir / "_summary.json").write_text(
        json.dumps(sheet_summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"✔ Reviews gespeichert → {rdir}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 4:
        print("Usage: python -m src.llm.critique exercises.json solutions/v1 reviews/v1")
        raise SystemExit(1)
    critique_sheet(sys.argv[1], sys.argv[2], sys.argv[3])
