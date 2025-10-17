import json
from pathlib import Path
from collections import defaultdict

LIB_PATH = Path("/Users/tim/NoteDeck/MainDeck-modular/Library/Library.json")
TOPICMAP_PATH = Path("/Users/tim/NoteDeck/MainDeck-modular/Library/SubjectsTopics.json")


# Lade vorhandenes TopicMap (wenn vorhanden)
if TOPICMAP_PATH.exists():
    with TOPICMAP_PATH.open(encoding="utf-8") as f:
        topicmap = json.load(f)
else:
    topicmap = {}

# Hilfsstruktur für automatische Indizierung
counters = {subj: d.get("index", 1) for subj, d in topicmap.items()}

# Lade Units
with LIB_PATH.open(encoding="utf-8") as f:
    units = json.load(f)

for unit in units:
    subj = unit.get("Subject", "").strip()
    topic = unit.get("Topic", "").strip()
    parent = unit.get("ParentTopic", None)
    litid = unit.get("LitID", "").strip()

    if not subj or not topic:
        continue  # Ungültig, überspringen

    subj_entry = topicmap.setdefault(subj, {"index": counters.get(subj, 1), "topics": {}})
    topics = subj_entry["topics"]

    if topic not in topics:
        index = subj_entry["index"]
        topics[topic] = {
            "index": index,
            "parent": parent,
            "litIDs": {}
        }
        subj_entry["index"] += 1
    else:
        if parent and not topics[topic].get("parent"):
            topics[topic]["parent"] = parent

    if litid:
        lit_map = topics[topic].setdefault("litIDs", {})
        if litid not in lit_map:
            topic_id = f"{subj}-{litid}-{topics[topic]['index']:02d}"
            lit_map[litid] = topic_id

# Finales Schreiben
with TOPICMAP_PATH.open("w", encoding="utf-8") as f:
    json.dump(topicmap, f, indent=2, ensure_ascii=False)

print("✅ SubjectsTopics.json wurde erfolgreich aktualisiert.")
