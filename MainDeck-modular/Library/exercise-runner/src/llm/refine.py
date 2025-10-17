# src/llm/refine.py
import json
from pathlib import Path
from src.llm.client import get_client, get_model

REFINE_SYS = (
    "Du verbesserst eine vorhandene LaTeX-Lösung anhand eines strukturierten Reviews.\n"
    "STIL & FORM:\n"
    "- Antworte ausschließlich mit LaTeX-Text (kein Markdown, keine Listen 1./-/*, kein Fettdruck).\n"
    "- Mathematisch-dominanter Stil: Herleitungen in Umgebungen wie align*, equation, gather*.\n"
    "- Prosa nur zur kurzen Begründung einzelner Schritte (max. 1–2 Sätze zwischen Blöcken).\n"
    "- Gleichungen nur nummerieren, wenn sie referenziert werden; sonst * aus den Umgebungen nutzen.\n"
    "- Konsistente Notation mit der Vorversion; nur korrigieren, wenn nötig.\n"
    "- Keine Wiederholung der Aufgabenstellung.\n"
    "- Nutze Tex-Kommentare (% ...) für sehr kurze Meta-Hinweise statt Fließtext, falls nötig."
)


# PROMPT_TEMPLATE = """Aufgabe {sid}.
# Vorherige Lösung (TeX):
# ---BEGIN-SOLUTION---
# {solution}
# ---END-SOLUTION---

# Review (JSON):
# ---BEGIN-REVIEW---
# {review}
# ---END-REVIEW---

# Erzeuge eine verbesserte Lösung als reinen TeX-Body. Behalte korrekte Passagen,
# füge präzise Begründungen ein, korrigiere Fehler und vermeide redundanten Text.
# """

PROMPT_TEMPLATE = r"""Aufgabe {sid}.

Vorherige Lösung (TeX):
%% --- BEGIN SOLUTION ---
{solution}
%% --- END SOLUTION ---

Review (JSON):
%% --- BEGIN REVIEW ---
{review}
%% --- END REVIEW ---

AUFTRAG:
- Arbeite JEDE Schwäche/Fix-Suggestion konkret ein, primär über mathematische Schritte/Formeln.
- Ergänze fehlende Zwischenschritte explizit (Ableitungen, Identitäten, Umformungen, Randfälle).
- Bevorzuge Herleitungen in align* / equation*; Prosa minimal (höchstens 1–2 Sätze pro Abschnitt).
- Behalte korrekte Teile der alten Lösung; ersetze nur fehlerhafte Passagen.
- Wenn Invarianz/Erhaltungssätze gefordert sind: formuliere zuerst die exakte mathematische Aussage, dann zeige sie rechnerisch.
- Falls Definitionen nötig sind (z.B. Variablentransformationen, Delta-Funktion unter Lorentz-Transformation): gib die Definition/Transformationsregel als Formel an und benutze sie unmittelbar.

AUSGABE:
- Nur den neuen TeX-Body (keine Präambel, kein \\begin{{document}}).
- Struktur: kurze einleitende 1–2 Sätze (optional), dann die korrigierte Herleitung als zusammenhängender Mathematikblock.
- Füge optional am Ende ein kurzes %CHECK-Kommentar (1–3 Zeilen) ein, das zeigt, welche Review-Punkte du explizit adressiert hast.
"""
# Ende


def refine_sheet(ex_json: str, prev_sol_dir: str, review_dir: str, new_sol_dir: str):
    """
    Für jede (Unter-)Aufgabe:
      - liest Lösung aus prev_sol_dir (z.B. solutions/v1)
      - liest Review aus review_dir (z.B. reviews/v1)
      - schreibt verbesserte Lösung nach new_sol_dir (z.B. solutions/v2)
    """
    client = get_client()
    model = get_model("refine", "gpt-4o-mini")

    data = json.loads(Path(ex_json).read_text(encoding="utf-8"))
    prev_dir = Path(prev_sol_dir)
    rev_dir = Path(review_dir)
    out_dir = Path(new_sol_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Hauptaufgaben + Subtasks
    for main in data["tasks"]:
        subs = main.get("subtasks", [])
        if subs:
            for sub in subs:
                sid = sub["sub_id"]  # z.B. "1.1"
                sol_path = prev_dir / f"{sid}.tex"
                rev_path = rev_dir / f"{sid}.json"
                if not sol_path.exists() or not rev_path.exists():
                    # nichts zu tun; optional alte Lösung rüberkopieren
                    # (out_dir / f"{sid}.tex").write_text(sol_path.read_text(encoding="utf-8")) if sol_path.exists() else None
                    continue

                prompt = PROMPT_TEMPLATE.format(
                    sid=sid,
                    solution=sol_path.read_text(encoding="utf-8"),
                    review=Path(rev_path).read_text(encoding="utf-8"),
                )
                resp = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": REFINE_SYS},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.2,
                )
                refined = resp.choices[0].message.content.strip()
                (out_dir / f"{sid}.tex").write_text(refined, encoding="utf-8")
        else:
            # Hauptaufgabe ohne Subtasks
            tid = main["task_id"]
            sol_path = prev_dir / f"{tid}.tex"
            rev_path = rev_dir / f"{tid}.json"
            if not sol_path.exists() or not rev_path.exists():
                continue

            prompt = PROMPT_TEMPLATE.format(
                sid=tid,
                solution=sol_path.read_text(encoding="utf-8"),
                review=Path(rev_path).read_text(encoding="utf-8"),
            )
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": REFINE_SYS},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
            )
            refined = resp.choices[0].message.content.strip()
            (out_dir / f"{tid}.tex").write_text(refined, encoding="utf-8")

    print(f"✔ Refined-Lösungen → {out_dir}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 5:
        print("Usage: python -m src.llm.refine exercises.json solutions/v1 reviews/v1 solutions/v2")
        raise SystemExit(1)
    refine_sheet(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
