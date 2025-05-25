import json
import uuid

# Pfad zur Library.json
LIBRARY_PATH = "/Users/tim/NoteDeck/MainDeck-modular/Library/Library.json"

# Lade bestehende Daten
with open(LIBRARY_PATH, "r", encoding="utf-8") as f:
    library = json.load(f)

# Zähle, wie viele ergänzt werden müssen
missing_uid_count = 0
for unit in library:
    if "UID" not in unit:
        unit["UID"] = str(uuid.uuid4())
        missing_uid_count += 1

# Speichern der aktualisierten Datei
with open(LIBRARY_PATH, "w", encoding="utf-8") as f:
    json.dump(library, f, indent=2, ensure_ascii=False)

print(f"Fertig. {missing_uid_count} Units erhielten eine neue UID.")


import json
from collections import Counter

with open("Library.json", "r", encoding="utf-8") as f:
    data = json.load(f)

uids = [entry["UID"] for entry in data if "UID" in entry]
counter = Counter(uids)
duplicates = [uid for uid, count in counter.items() if count > 1]

print(f"Total: {len(uids)} UIDs, Duplicates: {len(duplicates)}")
if duplicates:
    print("⚠️ Doppelte UIDs gefunden:", duplicates)
else:
    print("✅ Alle UIDs sind eindeutig.")
