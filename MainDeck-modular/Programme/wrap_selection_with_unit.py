# wrap_selection_with_unit.py
from pathlib import Path
import sys

print("🧩 LaTeX Unit-Wrap Tool gestartet")

if len(sys.argv) != 3:
    print("❗ Aufruf: python wrap_selection_with_unit.py <filename> <selection_file>")
    sys.exit(1)

tex_file = Path(sys.argv[1])
sel_file = Path(sys.argv[2])

if not tex_file.exists() or not sel_file.exists():
    sys.exit("❌ Datei nicht gefunden.")

# Gelesener Textblock aus temporärer Datei (z. B. vom Makro gespeichert)
selection = sel_file.read_text(encoding="utf-8").strip()
if not selection:
    sys.exit("❌ Kein markierter Text gefunden.")

print(f"✏️  Markierter Text:\n{'-'*40}\n{selection}\n{'-'*40}")

unit_id = input("🔢 Gib die UnitID ein (z. B. ALG-1-02-03): ").strip()
if not unit_id:
    sys.exit("❌ Keine UnitID eingegeben.")

wrapped = f"""
\\begin{{unit}}{{{unit_id}}}
{selection}
\\end{{unit}}
"""

content = tex_file.read_text(encoding="utf-8")
if selection not in content:
    sys.exit("❌ Der markierte Text wurde in der Datei nicht gefunden.")

new_content = content.replace(selection, wrapped)
tex_file.write_text(new_content, encoding="utf-8")

print("✅ Text ersetzt und gespeichert.")
