#!/usr/bin/env python3
"""
module_exporter.py
Extrahiert alle Content‑Units aus Library.tex in einzelne Modul‑Dateien
unter Library/Module/<UnitID>.tex
"""

from pathlib import Path
import re
import shutil

# -------------------------------------------------- Pfade
BASE_DIR   = Path("Library")              # Übergeordneter Library‑Ordner
SRC_TEX    = BASE_DIR / "Library.tex"     # Quelle
MOD_DIR    = BASE_DIR / "Module"          # Zielordner für Module

# -------------------------------------------------- Zielordner vorbereiten
if MOD_DIR.exists():
    shutil.rmtree(MOD_DIR)                # alles löschen (clean‑build)
MOD_DIR.mkdir(parents=True, exist_ok=True)

# -------------------------------------------------- Library.tex lesen
if not SRC_TEX.exists():
    raise FileNotFoundError(f"{SRC_TEX} nicht gefunden")

src = SRC_TEX.read_text(encoding="utf-8")

# -------------------------------------------------- Blöcke per RegEx finden
block_pat = re.compile(
    r"\\begin\{(\w+)\}\{([^}]+)\}\{([^}]*)\}(.*?)\\end\{\1\}",
    re.S
)

count = 0
for match in block_pat.finditer(src):
    env, unit_id, title, body = match.groups()
    module_tex = (
        f"% Auto‑generiert aus Library.tex\n"
        f"% UnitID: {unit_id}\n"
        f"% Titel : {title}\n\n"
        f"\\begin{{{env}}}{{{unit_id}}}{{{title}}}\n"
        f"{body.strip()}\n"
        f"\\end{{{env}}}\n"
    )
    (MOD_DIR / f"{unit_id}.tex").write_text(module_tex, encoding="utf-8")
    count += 1

print(f"✅  {count} Module in {MOD_DIR} erzeugt/überschrieben.")
