
from pathlib import Path
import csv, re

images_root = Path("/Users/tim/NoteDeck/MainDeck-modular/Library/Images")
csv_path = images_root / "Art" / "art_index.csv"

def normalize_artist(a: str) -> str:
    if not a: return a
    a = a.replace("_", " ").strip()
    m = re.match(r"^(?:Paintings|Works|Artworks|Drawings|Photographs|Sculptures)\s+by\s+(.+)$", a, re.I)
    return m.group(1) if m else a

rows = []
with csv_path.open(newline="", encoding="utf-8") as f:
    r = csv.DictReader(f)
    for row in r:
        old = row.get("artist","")
        new = normalize_artist(old)
        if new != old:
            row["artist"] = new
        rows.append(row)

with csv_path.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=[
        "uid","filename","artist","title","year","source","license","movement","keywords"
    ])
    w.writeheader()
    w.writerows(rows)

print("✔ CSV artists normalized. Examples:",
      [ (r["uid"], r["artist"]) for r in rows[:3] ])