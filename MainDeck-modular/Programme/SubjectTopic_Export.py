import json
import pandas as pd
from openpyxl import load_workbook

# --- Einstellungen ---
json_path = "../Library/SubjectsTopics.json"
excel_path = "TimeMonitoring.xlsx"
sheet_name = "Topics"

# JSON laden
with open(json_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# Daten extrahieren
rows = []
for subject, subject_data in data.items():
    for topic, meta in subject_data.get("topics", {}).items():
        rows.append({
            "Subject": subject,
            "ParentTopic": meta.get("parent"),
            "Topic": topic,
            "Index": meta.get("index")
        })

df = pd.DataFrame(rows).sort_values(by=["Subject", "Index"])

# Wenn Datei existiert: nur bestimmtes Sheet ersetzen
try:
    book = load_workbook(excel_path)
    with pd.ExcelWriter(excel_path, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
        writer.book = book
        df.to_excel(writer, sheet_name=sheet_name, index=False)
except FileNotFoundError:
    # Wenn Datei noch nicht existiert → neu erstellen
    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name=sheet_name, index=False)
