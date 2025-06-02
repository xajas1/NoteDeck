import json
from pathlib import Path

# === PARAMETER ANPASSEN ===
subject_filter = "EFT1"   # z. B. "QM"
old_litid = "T12"       # z. B. alte LitID in UnitID
new_litid = "K25a"       # neue LitID (auch tatsächlicher Wert in 'LitID'-Feld)

# === DATEIPFAD ZUR Library.json ===
library_path = Path("/Users/tim/NoteDeck/MainDeck-modular/Library/Library.json")


# === DATEN LADEN ===
with library_path.open("r", encoding="utf-8") as f:
    data = json.load(f)

# === EINTRÄGE AKTUALISIEREN ===
updated = 0
for unit in data:
    if (
        unit.get("Subject") == subject_filter and
        unit.get("LitID") == new_litid and
        old_litid in unit.get("UnitID", "")
    ):
        unit["UnitID"] = unit["UnitID"].replace(old_litid, new_litid, 1)
        updated += 1

# === SPEICHERN ===
with library_path.open("w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"✅ {updated} UnitIDs in Subject '{subject_filter}' ersetzt: '{old_litid}' → '{new_litid}'")
