import json

# === Dateipfade ===
library_path = "library.json"
topics_path = "SubjectsTopics.json"
output_path = "library_updated.json"

# === Dateien laden ===
with open(library_path, "r", encoding="utf-8") as f:
    library = json.load(f)

with open(topics_path, "r", encoding="utf-8") as f:
    subject_topics = json.load(f)

# === Units durchgehen und Topic-ID in UnitID korrigieren ===
for unit in library:
    subj = unit.get("Subject")
    topic = unit.get("Topic")
    litid = unit.get("LitID")

    if subj in subject_topics and topic in subject_topics[subj]["topics"]:
        topic_entry = subject_topics[subj]["topics"][topic]
        topic_id = topic_entry["litIDs"].get(litid)

        if topic_id:
            # Hole alte ID-Endung (z. B. "05" aus "A-S23-03-05")
            old_parts = unit["UnitID"].split("-")
            if len(old_parts) == 4:
                last_part = old_parts[3]
                # Neue UnitID mit korrektem TopicID + alter Endung
                unit["UnitID"] = f"{topic_id}-{last_part}"
                unit["ParentTopic"] = topic_entry["parent"]
                unit["TopicPath"] = f"{topic_entry['parent']}/{topic}"

# === Ergebnis speichern ===
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(library, f, indent=2, ensure_ascii=False)

print("✔️ Topic-Index in UnitIDs aktualisiert.")
print(f"📄 Gespeichert unter: {output_path}")
