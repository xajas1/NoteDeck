


Snip









# 🎨 Art-DB Starter — Quick Commands

## 1. Neues Setup (z. B. nach Code-Änderungen oder Datenbank-Reset)
Wechsle ins Programmverzeichnis:
```bash
cd /Users/tim/NoteDeck/MainDeck-modular/Programme/art-db-starter
```

Datenbank + Galerien neu aufbauen (kein Download):
```bash
python art_wiki.py --rebuild-only --artist-standalone
```

➡ erzeugt `.tex`-Galerien pro Künstler im Ordner `Library/Images/Art/` (bzw. `Art_TeX/` für LaTeX).

---

## 2. Bilder für **einen Künstler** von Wikidata holen
Beispiel: 50 Werke von Vincent van Gogh:
```bash
python art_wiki.py --artist "Vincent van Gogh" --limit 50
```
python art_wiki.py --artist "Camille Pissarro" --limit 50

---

## 3. Bilder für **ein Werk** holen
Beispiel: „The Starry Night“ von Vincent van Gogh:
```bash
python art_wiki.py --work "The Starry Night" --work-artist "Vincent van Gogh" --limit 3
```

---

## 4. Bilder aus **Commons-Kategorie** holen
Beispiel: Kategorie „Paintings by Hilma af Klint“:
```bash
python art_wiki.py --commons-category "Paintings_by_Hilma_af_Klint" --limit 20
```

---

## 5. Einzelne Datei von Wikimedia Commons holen
Beispiel: `File:Vincent_van_Gogh_-_Sunflowers.jpg`:
```bash
python art_wiki.py --commons-file "Vincent_van_Gogh_-_Sunflowers.jpg" --work-artist "Vincent van Gogh"
```

---

## 6. Nur TeX-Galerien neu generieren (keine neuen Downloads)
Alle Galerien neu rendern:
```bash
python art_wiki.py --rebuild-only
```

Nur pro-Künstler-Galerien mit Header:
```bash
python art_wiki.py --rebuild-only --artist-standalone
```

---

## 7. Galerie-Dateien finden
- **CSV-Datenbank:**  
  `Library/Images/Art/art_index.csv`  
- **Originalbilder:**  
  `Library/Images/Art/`  
- **LaTeX-optimierte Bilder:**  
  `Library/Images/Art_TeX/`  
- **Galerien (.tex):**  
  `Library/Images/Art/*.tex`  

---

👉 Tipp: Falls ein Download fehlschlägt, prüfe im Log (`[warn] ...`) und lösche ggf. kaputte Dateien aus `Art/` oder `Art_TeX`, dann neu starten.
