from pathlib import Path
from PIL import Image

# Pfade anpassen
images_root = Path("/Users/tim/NoteDeck/MainDeck-modular/Library/Images")
art_dir = images_root / "Art"
tex_dir = images_root / "Art_TeX"
tex_dir.mkdir(parents=True, exist_ok=True)

count = 0
for img_path in art_dir.glob("**/*"):
    if img_path.is_file() and img_path.suffix.lower() in (".jpg", ".jpeg", ".png", ".tif", ".tiff"):
        tex_path = tex_dir / img_path.name
        if tex_path.exists():
            continue  # schon vorhanden
        
        try:
            with Image.open(img_path) as im:
                im.thumbnail((1600, 1600), Image.LANCZOS)
                im.save(tex_path, quality=85, optimize=True)
                count += 1
                print(f"[+] Kopie erstellt: {tex_path.name}")
        except Exception as e:
            print(f"[!] Fehler bei {img_path.name}: {e}")

print(f"\nFertig. {count} neue TeX-Kopien erstellt.")
