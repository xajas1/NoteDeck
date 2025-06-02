import json
from pathlib import Path

# === Parameter anpassen ===
subject_to_update = "EFT1"       # z.B. "QM"
old_litid = "K25"              # aktuelle LitID
new_litid = "K25a"              # neue LitID

# === Pfad zur Library.json ===
library_path = Path("/Users/tim/NoteDeck/MainDeck-modular/Library/Library.json")

# === JSON laden ===
if not library_path.exists():
    raise FileNotFoundError(f"❌ Datei nicht gefunden: {library_path}")

with library_path.open("r", encoding="utf-8") as f:
    library_data = json.load(f)

# === Aktualisieren ===
count = 0
for unit in library_data:
    if unit.get("Subject") == subject_to_update and unit.get("LitID") == old_litid:
        unit["LitID"] = new_litid
        count += 1

# === Speichern ===
with library_path.open("w", encoding="utf-8") as f:
    json.dump(library_data, f, indent=2, ensure_ascii=False)

print(f"✅ {count} Einträge in Subject '{subject_to_update}' geändert von LitID '{old_litid}' → '{new_litid}'")
