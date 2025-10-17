import json

# === Dateipfade anpassen ===
library_path = "/Users/tim/NoteDeck/MainDeck-modular/Library/Library.json"
topics_path = "/Users/tim/NoteDeck/MainDeck-modular/Library/SubjectsTopics.json"
output_path = "/Users/tim/NoteDeck/MainDeck-modular/Library/Library_updated.json"
backup_path = "/Users/tim/NoteDeck/MainDeck-modular/Library/Library_backup.json"

# === Daten laden ===
with open(library_path, "r", encoding="utf-8") as f:
    library = json.load(f)

with open(topics_path, "r", encoding="utf-8") as f:
    subject_topics = json.load(f)

# === Backup speichern ===
with open(backup_path, "w", encoding="utf-8") as f:
    json.dump(library, f, indent=2, ensure_ascii=False)

# === Verarbeitung starten ===
updates = []
subject_filter = "A"
litid_filter = "S23"

for unit in library:
    subj = unit.get("Subject")
    topic = unit.get("Topic")
    litid = unit.get("LitID")

    # Nur bestimmte Kombinationen anfassen
    if subj != subject_filter or litid != litid_filter:
        continue

    topics = subject_topics.get(subj, {}).get("topics", {})
    topic_info = topics.get(topic)

    if not topic_info:
        continue

    topic_id = topic_info.get("litIDs", {}).get(litid)
    if not topic_id:
        continue

    # Aktuelle UnitID analysieren
    unit_id = unit.get("UnitID", "")
    parts = unit_id.split("-")
    if len(parts) != 4:
        continue  # unerwartete Struktur

    # Setze neue UnitID mit alter Endziffer
    running = parts[3]
    new_unit_id = f"{topic_id}-{running}"

    if new_unit_id != unit_id:
        updates.append((unit_id, new_unit_id))
        unit["UnitID"] = new_unit_id

    # Ergänze strukturierte Pfade
    unit["ParentTopic"] = topic_info.get("parent", "")
    unit["TopicPath"] = f"{topic_info.get('parent', '')}/{topic}"

# === Speichern ===
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(library, f, indent=2, ensure_ascii=False)

# === Ausgabe anzeigen ===
print(f"✔️ {len(updates)} UnitIDs wurden angepasst (nur A + S23).\n")
for old, new in updates:
    print(f"🔁 {old} → {new}")

print(f"\n📄 Gespeichert in: {output_path}")
print(f"🗂️  Backup unter: {backup_path}")
