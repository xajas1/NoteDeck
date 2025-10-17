#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flatten Images/Art into a single folder (no subfolders) and build a copy-paste gallery.
- Moves/copies all images from Images/Art/** into Images/Art/
- Ensures unique, clean basenames (prefer UID__Artist__Title__Year.ext)
- Updates art_index.csv so 'filename' becomes just the basename
- Writes art_gallery.tex (standalone), 8 images per page, sorted by artist
"""

import os, re, csv, argparse, shutil
from pathlib import Path
from textwrap import shorten

IMG_EXT = {".jpg",".jpeg",".png",".tif",".tiff",".webp"}

def slug(s: str) -> str:
    if s is None: s = ""
    rep = {"ä":"ae","ö":"oe","ü":"ue","ß":"ss","Ä":"Ae","Ö":"Oe","Ü":"Ue"}
    for k,v in rep.items(): s = s.replace(k,v)
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"[^A-Za-z0-9]+","_", s).strip("_")
    return s or "untitled"

def esc_tex(s: str) -> str:
    if s is None: s = ""
    for k,v in {
        "\\":"\\textbackslash{}", "{":"\\{","}":"\\}",
        "#":"\\#","%":"\\%","&":"\\&","_":"\\_",
        "~":"\\textasciitilde{}","^":"\\textasciicircum{}",
    }.items():
        s = s.replace(k,v)
    return s

def ensure_index(csv_path: Path):
    if not csv_path.exists():
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=["uid","filename","artist","title","year","source","license","movement","keywords"]).writeheader()

def read_rows(csv_path: Path):
    ensure_index(csv_path)
    with csv_path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def write_rows(csv_path: Path, rows):
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["uid","filename","artist","title","year","source","license","movement","keywords"])
        w.writeheader(); w.writerows(rows)

def next_uid(rows):
    mx = 0
    for r in rows:
        m = re.match(r"ART(\d+)$", r.get("uid",""))
        if m: mx = max(mx, int(m.group(1)))
    return f"ART{mx+1:04d}"

def unique_path(p: Path) -> Path:
    if not p.exists(): return p
    i = 2
    base = p.stem; ext = p.suffix
    while True:
        q = p.with_name(f"{base}-{i}{ext}")
        if not q.exists(): return q
        i += 1

def parse_from_basename(name: str):
    """
    Try to parse UID, artist, title, year from a basename like:
      ART0123__Paul_Klee__Stricken_City__1936.jpg
    Returns (uid, artist, title, year)
    """
    stem = Path(name).stem
    parts = stem.split("__")
    uid, artist, title, year = "", "", "", ""
    if parts and re.fullmatch(r"ART\d{4,}", parts[0] or ""):
        uid = parts[0]
        if len(parts) >= 2: artist = parts[1].replace("_"," ").strip()
        if len(parts) >= 3: title  = parts[2].replace("_"," ").strip()
        if len(parts) >= 4: year   = parts[3].strip()
    return uid, artist, title, year

def build_basename(uid, artist, title, year, ext):
    artist_s = slug(artist)[:60]
    title_s  = slug(title)[:90]
    year_s   = slug(year) if year else ""
    if year_s:
        return f"{uid}__{artist_s}__{title_s}__{year_s}{ext}"
    else:
        return f"{uid}__{artist_s}__{title_s}{ext}"

def flatten_and_update(art_dir: Path, csv_path: Path, move: bool):
    rows = read_rows(csv_path)
    # Map by UID for quick updates
    by_uid = {r["uid"]: r for r in rows if r.get("uid")}
    # Collect all images recursively (including root)
    files = [p for p in art_dir.rglob("*") if p.is_file() and p.suffix.lower() in IMG_EXT]
    # Keep root flat target
    moved = 0
    new_rows = rows.copy()
    have_uid = {r["uid"] for r in rows if r.get("uid")}
    for p in files:
        if p.parent == art_dir:
            # already flat: ensure CSV filename is basename only
            # find row by uid from filename if possible
            uid_guess, _, _, _ = parse_from_basename(p.name)
            if uid_guess and uid_guess in by_uid:
                r = by_uid[uid_guess]; r["filename"] = p.name
            continue
        # prepare metadata
        uid, artist, title, year = parse_from_basename(p.name)
        ext = p.suffix.lower().replace(".jpeg",".jpg").replace(".tiff",".tif")
        if not uid:
            # try CSV match by full relative path
            rel = p.relative_to(art_dir.parent.parent) if False else None
            # fallback: assign new uid
            uid = next_uid(new_rows)
        # Look up CSV row or create one
        row = by_uid.get(uid)
        if not row:
            row = {"uid": uid, "filename":"", "artist": artist, "title": title, "year": year,
                   "source":"", "license":"", "movement":"", "keywords":""}
            new_rows.append(row); by_uid[uid] = row
        # Build clean basename
        base = build_basename(uid, row.get("artist") or artist, row.get("title") or title, row.get("year") or year, ext)
        target = unique_path(art_dir / base)
        # move/copy
        target.parent.mkdir(parents=True, exist_ok=True)
        if move:
            shutil.move(str(p), str(target))
        else:
            shutil.copy2(str(p), str(target))
        row["filename"] = target.name  # flat basename only
        moved += 1
    # Write updated CSV
    write_rows(csv_path, new_rows)
    return moved, new_rows

def write_gallery(art_dir: Path, rows, per_page: int = 8, fname: str = "art_gallery.tex"):
    # sort by artist (casefold), then title
    rows2 = sorted(rows, key=lambda r: ((r.get("artist") or "").casefold(), (r.get("title") or "").casefold()))
    # standalone gallery (can be compiled alone, lives in same folder as images)
    lines = []
    lines += [
        r"\documentclass[10pt]{article}",
        r"\usepackage[margin=1.6cm]{geometry}",
        r"\usepackage{graphicx,xcolor}",
        r"\usepackage{array,ragged2e,caption}",
        r"\captionsetup{font=small,labelformat=empty}",
        r"\setlength{\parindent}{0pt}",
        r"\title{Art Gallery (copy & paste)}",
        r"\date{}",
        r"\begin{document}",
        r"\maketitle",
        r"\vspace{-1em}",
        r"\small Tip: copy the code line under any picture into your document.",
        r"\normalsize",
        ""
    ]
    def mkcap(r):
        cap = f'{r.get("artist","")}, {r.get("title","")}'
        y = (r.get("year") or "").strip()
        if y: cap += f" ({y})"
        return cap
    # 4 columns (2 rows per page = 8 pics)
    cols = 4
    w = "{%s}" % ("m{.24\\textwidth}" * cols)
    i = 0
    lines += [r"\begin{center}"]
    lines += [r"\begin{tabular}" + w]
    for r in rows2:
        fn = r.get("filename","")
        if not fn: continue
        cap = mkcap(r)
        cap_verb = cap.replace("|","-")  # avoid verbatim | issues
        # cell content: image, caption, code line
        cell = [
            fr"\begin{{minipage}}{{.24\textwidth}}",
            fr"\centering\includegraphics[width=\linewidth]{{{fn}}}",
            fr"\vspace{{0.3ex}}",
            fr"{{\footnotesize\itshape {esc_tex(cap)}}}\\[-0.2ex]",
            fr"{{\scriptsize\ttfamily \string\StructurePic{{{fn}}}{{{esc_tex(cap)}}}{{...}}}}",
            r"\end{minipage}"
        ]
        lines += ["\n".join(cell)]
        i += 1
        if i % cols != 0:
            lines += [" & "]
        else:
            lines += [r"\\[1.4ex]"]
        if i % per_page == 0:
            lines += [r"\end{tabular}", r"\end{center}", r"\newpage", r"\begin{center}", r"\begin{tabular}"+w]
    # close last table
    if i % per_page != 0:
        lines += [r"\end{tabular}", r"\end{center}"]
    else:
        lines += []
    lines += [r"\end{document}"]
    (art_dir / fname).write_text("\n".join(lines), encoding="utf-8")
    return art_dir / fname

def main():
    ap = argparse.ArgumentParser(description="Flatten Art images and build a copy-paste gallery.")
    ap.add_argument("--images-root", default="/Users/tim/NoteDeck/MainDeck-modular/Library/Images")
    ap.add_argument("--move", action="store_true", help="move (not copy) files into flat folder")
    ap.add_argument("--per-page", type=int, default=8)
    args = ap.parse_args()

    images_root = Path(args.images_root).expanduser().resolve()
    art_dir = images_root / "Art"
    art_dir.mkdir(parents=True, exist_ok=True)
    csv_path = art_dir / "art_index.csv"

    moved, rows = flatten_and_update(art_dir, csv_path, move=True or args.move)
    gal = write_gallery(art_dir, rows, per_page=args.per_page)
    print(f"Flattened/moved: {moved} files")
    print(f"CSV updated: {csv_path}")
    print(f"Gallery: {gal}")

if __name__ == "__main__":
    main()
