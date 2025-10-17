import json
from collections import defaultdict
from pathlib import Path

LIBRARY_PATH = Path("/Users/tim/NoteDeck/MainDeck-modular/Library/Library.json")
OUTPUT_PATH = Path("/Users/tim/NoteDeck/MainDeck-modular/Library/SubjectsTopics.json")

with LIBRARY_PATH.open("r", encoding="utf-8") as f:
    units = json.load(f)

structure = defaultdict(lambda: {
    "index": None,
    "topics": {}
})

subject_counter = 1

for unit in units:
    subj = unit["Subject"]
    topic = unit["Topic"]
    parent = unit.get("ParentTopic") or None

    if structure[subj]["index"] is None:
        structure[subj]["index"] = subject_counter
        subject_counter += 1

    if topic not in structure[subj]["topics"]:
        next_index = len(structure[subj]["topics"]) + 1
        structure[subj]["topics"][topic] = {
            "index": next_index,
            "parent": parent
        }

with OUTPUT_PATH.open("w", encoding="utf-8") as f:
    json.dump(structure, f, indent=2, ensure_ascii=False)

print("✅ SubjectsTopics.json successfully created.")
