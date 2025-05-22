from pathlib import Path
import json

# Pfad zur Library.json
BASE_DIR = Path(__file__).resolve().parents[1]
LIB_JSON = BASE_DIR / "Library" / "Library.json"

# Backup-Datei zur Sicherheit
BACKUP_PATH = LIB_JSON.with_suffix(".bak.json")

def add_body_placeholders():
    if not LIB_JSON.exists():
        print("❌ Library.json nicht gefunden.")
        return

    # Originaldatei laden
    with LIB_JSON.open("r", encoding="utf-8") as f:
        data = json.load(f)

    modified = False
    for entry in data:
        if "Body" not in entry:
            entry["Body"] = "% TODO: Inhalt ergänzen (Tex)"
            modified = True

    if not modified:
        print("ℹ️ Keine Änderungen notwendig – alle Einträge haben bereits ein Body-Feld.")
        return

    # Backup anlegen
    BACKUP_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"📦 Backup gespeichert unter: {BACKUP_PATH}")

    # Aktualisierte Datei schreiben
    with LIB_JSON.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✅ Body-Felder hinzugefügt und gespeichert in: {LIB_JSON}")

if __name__ == "__main__":
    add_body_placeholders()
