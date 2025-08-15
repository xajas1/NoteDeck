
# art_wiki.py – Kunstbilder aus Wikicommons & Wikidata laden

Dieses Skript lädt Bilder von Kunstwerken (Gemälde, Zeichnungen, Skulpturen …) aus Wikimedia Commons oder Wikidata, speichert sie lokal, aktualisiert einen Bildindex (`art_index.csv`) und erzeugt eine LaTeX-Galerie (`art_gallery.tex`).

## 📦 Voraussetzungen

- **Python 3.8+**
- Abhängigkeiten installieren:
  ```bash
  pip install -r requirements.txt
  ```
- Internetverbindung (Zugriff auf Wikimedia/Wikidata API)
- Zielordner:  
  Standardmäßig werden Dateien unter  
  ```
  MainDeck-modular/Library/Images/Art/
  ```
  gespeichert.

---

## 🔹 Nutzung

Das Skript kann auf zwei Arten arbeiten:

### 1. Nach **Commons-Kategorie** suchen (`--commons-category`)
Lädt Bilder aus einer bekannten Kategorie auf Wikimedia Commons.

```bash
python3 art_wiki.py --commons-category "Hilma_af_Klint" --limit 50 --min-width 1000 --min-height 1000 --standalone
```

**Parameter:**
- `--commons-category "NAME"`  
  Name der Commons-Kategorie (ohne „Category:“ Präfix).  
  Beispiel: `"Hilma_af_Klint"` oder `"Paintings_by_Hilma_af_Klint"`.
- `--limit N`  
  Max. Anzahl zu ladender Bilder.
- `--min-width N` / `--min-height N`  
  Mindestauflösung in Pixel (Bilder darunter werden übersprungen).
- `--standalone`  
  Erstellt eine eigenständige Galerie nur mit den neu geladenen Bildern (statt sie an bestehende Galerie anzuhängen).

---

### 2. Nach **Werk + Künstler** suchen (`--work` + `--work-artist`)
Sucht gezielt nach einem bestimmten Werk in Wikidata/Wikimedia Commons.

```bash
python3 art_wiki.py --work "Composition VII" --work-artist "Wassily Kandinsky" --limit 5

python3 art_wiki.py --work-artist "Wassily Kandinsky" --limit 5

python3 art_wiki.py --artist "Ernst Ludwig Kirchner" --limit 20

```

**Parameter:**
- `--work "Titel"`  
  Titel des Werks.
- `--work-artist "Name"`  
  Name des Künstlers.
- `--limit N`  
  Anzahl zu ladender Treffer.

---

## 📄 Ausgabe

Nach dem Lauf erstellt das Skript:
- **Bilder** im Zielordner `Images/Art/`
- **`art_index.csv`**: Metadaten aller gespeicherten Bilder (ID, Künstler, Titel, Auflösung, Quelle, …)
- **`art_gallery.tex`**: LaTeX-Galerie mit 6 Bildern pro Seite, gruppiert nach Künstler.

---

## ⚙️ Duplikat-Erkennung
- Das Skript nutzt **pHash** (perzeptueller Hash) zur Erkennung nahezu identischer Bilder.
- Standard-Schwellwert: `PHASH_DISTANCE_MAX = 5` (kann in Code angepasst werden).
- Optional: titelbasierte Duplikat-Erkennung (wenn implementiert) zur Vermeidung mehrfach hochgeladener Versionen desselben Werks.

---

## 💡 Tipps
- Verwende bei **Commons-Kategorien** möglichst präzise Kategorienamen.
- Mit hohen Werten bei `--min-width`/`--min-height` stellst du sicher, dass nur hochauflösende Bilder geladen werden.
- `--standalone` ist nützlich, wenn du nur eine Galerie für einen Künstler erzeugen möchtest.
- Wenn keine Bilder geladen werden, liegt das oft an:
  1. Falscher Kategoriebezeichnung
  2. Zu hohen Mindestmaßen
  3. Duplikat-Filter greift (Bild bereits vorhanden)
