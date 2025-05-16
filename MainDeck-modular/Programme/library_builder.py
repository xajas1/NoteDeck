from pathlib import Path
import pandas as pd
import json, re, sys
import math

# -------------------------------------------------- Konfiguration
EXCEL_FILE  = Path("../Stud-Monitoring-neu.xlsm")   # Pfad zur Excel‑Datei
QUERY_NAME  = "Abfrage"                             # Blatt / Tabelle der sortierten Query
HEADER_ROW  = 0                                     # Header befindet sich in Zeile 1

LIB_DIR  = Path("Library")
LIB_DIR.mkdir(exist_ok=True)

LIB_TEX  = LIB_DIR / "Library.tex"
LIB_JSON = LIB_DIR / "Library.json"

ADDITIONAL = ["Layer", "Comp", "RelInt", "RelId", "Cont", "Cint", "CID"]

ENV = {  # CTyp → LaTeX‑Environment
    "DEF": "DEF",  "EXA": "EXA",  "PROP": "PROP",  "THEO": "THEO",
    "KORO": "KORO","LEM": "LEM",  "REM": "REM",   "STUD": "STUD",
    "PRF": "PRF",  "CONC": "CONC",
}

HEADER_MARK = "%-- AUTO-UNITS-START -------------------------------------------\n"
TAIL_MARK   = r"\pagebreak"        # Ende des Auto‑Bereichs (ggf. anpassen)

# -------------------------------------------------- Excel einlesen
print("📥  Lese Excel …")
try:
    df = pd.read_excel(EXCEL_FILE, sheet_name=QUERY_NAME, header=HEADER_ROW)
except ValueError as e:
    sys.exit(f"❌  {e}")

# Spalten‑Alias‑Mapping (robust gegen Groß/Klein)
aliases = {"unitid": "UnitID", "subject": "Subject", "topic": "Topic",
           "ctyp": "CTyp", "content": "Content"}
df.columns = [c.strip() for c in df.columns]
norm = {c.lower(): c for c in df.columns}
missing = [aliases[k] for k in aliases if k not in norm]
if missing:
    sys.exit(f"❌  Spalten fehlen: {missing}\nVorhanden: {list(df.columns)}")

base_cols = [norm[k] for k in aliases]
opt_cols  = [c for c in ADDITIONAL if c in df.columns]
df        = df[base_cols + opt_cols].dropna(subset=[norm["unitid"],
                                                   norm["ctyp"],
                                                   norm["content"]])

records = df.to_dict("records")

# -------------------------------------------------- Library.tex laden oder erstellen
if LIB_TEX.exists():
    tex_src = LIB_TEX.read_text(encoding="utf-8")
else:
    tex_src = ""

# Header bei Erst­erstellung einfügen
if HEADER_MARK not in tex_src:
    tex_src = r"""\documentclass[10pt, letterpaper]{article}
% … dein fixer Header …
""" + HEADER_MARK + TAIL_MARK + "\n\\end{document}\n"

# -------------------------------------------------- Auto‑Bereich herauslösen
try:
    head, tail = tex_src.split(HEADER_MARK, 1)
    auto, rest = tail.split(TAIL_MARK, 1)
except ValueError:
    sys.exit("❌  HEADER_MARK oder TAIL_MARK nicht gefunden – Library.tex prüfen")

block_pat = re.compile(r"\\begin\{\w+\}\{([^}]*)\}.*?\\end\{\w+\}\s*", re.S)
block_map = {m.group(1): m.group(0) for m in block_pat.finditer(auto)}

# -------------------------------------------------- Fehlende Units erzeugen
added = 0
for rec in records:
    uid = rec["UnitID"]
    if uid in block_map:         # bereits vorhanden
        continue
    env   = ENV.get(rec["CTyp"], "REM")
    title = str(rec["Content"]).strip()
    block_map[uid] = (f"\\begin{{{env}}}{{{uid}}}{{{title}}}\n"
                      f"% TODO: Inhalt ergänzen (Tex)\n"
                      f"\\end{{{env}}}\n\n")
    added += 1

# -------------------------------------------------- Reihenfolge exakt wie in Abfrage
excel_order = df[norm["unitid"]].tolist()         # bereits sortiert (Subject→Topic→Nr.)
for uid in block_map:                             # Alt‑IDs (falls vorhanden) anhängen
    if uid not in excel_order:
        excel_order.append(uid)

sorted_blocks = [block_map[uid] for uid in excel_order]
new_auto      = "".join(sorted_blocks)

# -------------------------------------------------- Library.tex zurückschreiben
tex_src = head + HEADER_MARK + new_auto + TAIL_MARK + rest
LIB_TEX.write_text(tex_src, encoding="utf-8")

if added:
    print(f"✅  {added} neue Units einsortiert.")
else:
    print("ℹ️  Keine fehlenden Units – Library.tex unverändert.")

# --------- NaN → None -------------------------------------------------
for rec in records:
    for k, v in rec.items():
        if isinstance(v, float) and math.isnan(v):
            rec[k] = None

# -------------------------------------------------- JSON komplett neu schreiben
with open(LIB_JSON, "w", encoding="utf-8") as fh:
    json.dump(records, fh, indent=2, ensure_ascii=False, allow_nan=False)

print(f"✅  Library.json vollständig überschrieben mit {len(records)} Einträgen.")

