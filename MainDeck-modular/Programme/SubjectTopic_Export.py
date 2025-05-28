import json
import pandas as pd
from pathlib import Path

# --- Einstellungen ---
json_path = Path("/Users/tim/NoteDeck/MainDeck-modular/Library/SubjectsTopics.json")
excel_path = Path("/Users/tim/NoteDeck/Monitoring/TimeMonitoring.xlsx")
sheet_name = "Topics"

# JSON laden
with open(json_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# Daten extrahieren (eine Zeile pro LitID)
rows = []
for subject, subject_data in data.items():
    for topic, meta in subject_data.get("topics", {}).items():
        litid_map = meta.get("litIDs", {})
        if litid_map:
            for litid, topicid in litid_map.items():
                rows.append({
                    "Subject": subject,
                    "ParentTopic": meta.get("parent"),
                    "Topic": topic,
                    "Index": meta.get("index"),
                    "LitID": litid,
                    "TopicID": topicid
                })
        else:
            rows.append({
                "Subject": subject,
                "ParentTopic": meta.get("parent"),
                "Topic": topic,
                "Index": meta.get("index"),
                "LitID": "",
                "TopicID": ""
            })

# DataFrame erstellen und sortieren
df = pd.DataFrame(rows).sort_values(by=["Subject", "Index", "LitID"])

# Ordner erstellen, falls nicht vorhanden
excel_path.parent.mkdir(parents=True, exist_ok=True)

# Excel schreiben (Sheet ersetzen oder Datei neu erzeugen)
try:
    with pd.ExcelWriter(excel_path, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
        df.to_excel(writer, sheet_name=sheet_name, index=False)
except FileNotFoundError:
    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name=sheet_name, index=False)

print("✅ Export abgeschlossen: Sheet 'Topics' aktualisiert.")
