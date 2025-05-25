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
