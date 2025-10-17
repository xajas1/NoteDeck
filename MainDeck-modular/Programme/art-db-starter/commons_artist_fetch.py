#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Commons-only Artist Fetcher (robust, recursive, PD/CC only).

Usage example:
  python3 commons_artist_fetch.py --artist "Wassily Kandinsky" --limit 400
"""

import os, re, csv, time, argparse, sys
from pathlib import Path
import requests

# ---------- config ----------
DEFAULT_IMAGES_ROOT = "/Users/tim/NoteDeck/MainDeck-modular/Library/Images"
UA = {"User-Agent": "NoteDeck-CommonsFetcher/1.0 (local)"}
ALLOWED_LIC = ("public domain","cc","cc0","cc-by","cc-by-sa","pdm")

# ---------- utils ----------
def resolve_images_root(cli_root: str|None) -> Path:
    if cli_root: return Path(cli_root).expanduser().resolve()
    env = os.environ.get("ART_IMAGES_ROOT")
    return Path(env).expanduser().resolve() if env else Path(DEFAULT_IMAGES_ROOT).expanduser().resolve()

def slug(s: str) -> str:
    if s is None: s = ""
    repl = {"ä":"ae","ö":"oe","ü":"ue","ß":"ss","Ä":"Ae","Ö":"Oe","Ü":"Ue"}
    for k,v in repl.items(): s = s.replace(k,v)
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"[^A-Za-z0-9]+", "_", s).strip("_")
    return s or "untitled"

def artist_folder(artist: str) -> str:
    a = (artist or "").strip()
    if not a or a.lower() in {"unknown","anonymous","unidentified","unknown maker"}:
        return "Unknown"
    if "," in a: last = a.split(",")[0].strip()
    else: last = (a.split() or ["Unknown"])[-1]
    return slug(last) or "Unknown"

def ensure_index(csv_path: Path):
    if not csv_path.exists():
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=[
                "uid","filename","artist","title","year","source","license","movement","keywords"
            ]).writeheader()

def read_rows(csv_path: Path):
    ensure_index(csv_path)
    with csv_path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def next_uid(rows):
    mx = 0
    for r in rows:
        m = re.match(r"ART(\d+)$", r.get("uid",""))
        if m: mx = max(mx, int(m.group(1)))
    return f"ART{mx+1:04d}"

def write_rows(csv_path: Path, rows):
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=[
            "uid","filename","artist","title","year","source","license","movement","keywords"
        ])
        w.writeheader(); w.writerows(rows)

def regenerate_tex(tex_path: Path, rows):
    def esc(s): 
        return (s or "").replace("\\","\\textbackslash{}").replace("{","\\{").replace("}","\\}")
    lines = ["% Auto-generated — DO NOT EDIT.", ""]
    uids = []
    for r in rows:
        uid = r["uid"]; uids.append(uid)
        cap = f'{r["artist"]}, {r["title"]} ({r["year"]})' if r["year"] else f'{r["artist"]}, {r["title"]}'
        lines += [
          fr"\providecommand{{\artpath@{uid}}}{{{esc(r['filename'])}}}",
          fr"\providecommand{{\artcap@{uid}}}{{{esc(cap)}}}",
          ""
        ]
    lines.append(r"\def\AllArtUIDs{" + ",".join(uids) + "}")
    tex_path.write_text("\n".join(lines), encoding="utf-8")

def make_sig(artist, title, year):  # dedupe key
    norm = lambda s: slug(str(s)).lower()
    return (norm(artist), norm(title), norm(year))

def load_seen(csv_path: Path):
    return { make_sig(r["artist"], r["title"], r["year"]) for r in read_rows(csv_path) }

def get_json(params, retries=3, sleep=0.8):
    url = "https://commons.wikimedia.org/w/api.php"
    for i in range(retries):
        try:
            r = requests.get(url, params=params, headers=UA, timeout=40)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            if i == retries-1:
                print("[warn] Commons request failed:", e)
                return {}
            time.sleep(sleep)
    return {}

# ---------- core ----------
def fetch_commons_artist(artist: str, limit: int, images_root: Path):
    art_dir = images_root / "Art"
    art_dir.mkdir(parents=True, exist_ok=True)
    csv_path = art_dir / "art_index.csv"
    tex_path = art_dir / "art_index.tex"
    ensure_index(csv_path)

    rows = read_rows(csv_path)
    seen = load_seen(csv_path)

    # Startkategorien (rekursiv):
    base_cats = [
        f"Category:Paintings by {artist}",
        f"Category:Watercolors by {artist}",
        f"Category:Drawings by {artist}",
        f"Category:Prints by {artist}",
        f"Category:Works by {artist}",
    ]

    # BFS durch Kategorien
    queue = []
    visited = set()
    # Nur Kategorien, die existieren, einreihen
    for cat in base_cats:
        test = get_json({
            "action":"query","format":"json","formatversion":2,
            "list":"search","srsearch":cat,"srnamespace":14,"srlimit":1
        })
        ok = bool((test.get("query") or {}).get("search"))
        if ok: queue.append(cat)
    if not queue:
        # Fallback: allgemeine Künstlersuche -> passende Kategorien nehmen
        sr = get_json({
            "action":"query","format":"json","formatversion":2,
            "list":"search","srsearch":artist,"srnamespace":14,"srlimit":20
        })
        for hit in (sr.get("query") or {}).get("search", []):
            title = hit.get("title","")
            if ("by " in title.lower()) or ("works" in title.lower()):
                queue.append(title)
    if not queue:
        print("Keine passenden Commons-Kategorien gefunden."); return

    saved = 0
    while queue and saved < limit:
        cat = queue.pop(0)
        if cat in visited: 
            continue
        visited.add(cat)
        print(f"[commons] scan: {cat}")

        # Dateien holen (paged)
        cont = None
        while saved < limit:
            params = {
              "action":"query","format":"json","formatversion":2,
              "generator":"categorymembers","gcmtitle":cat,
              "gcmnamespace":6,"gcmtype":"file","gcmlimit":50,
              "prop": "imageinfo",
                "iiprop": "url|mime|size|extmetadata",
                "iiextmetadatafilter": "LicenseShortName|Artist|ObjectName|Date",
                "iiurlwidth": 2048
            }
            if cont: params["gcmcontinue"] = cont
            data = get_json(params)
            pages = (data.get("query") or {}).get("pages") or []
            for p in pages:
                if saved >= limit: break
                ii = (p.get("imageinfo") or [{}])[0]
                url = ii.get("thumburl") or ii.get("url")
                if not url: continue
                meta = ii.get("extmetadata") or {}
                lic = (meta.get("LicenseShortName",{}).get("value","") or "").lower()
                if not any(k in lic for k in ALLOWED_LIC): 
                    continue

                title = (p.get("title","").replace("File:","")) or "Untitled"
                # Commons führt den Artist oft nicht -> erzwingen
                artist_name = artist
                year = re.sub(r".*?(\\b\\d{3,4}(?:[-/–]\\d{2,4})?).*", r"\\1", (meta.get("Date",{}).get("value","") or "")) or ""

                sig = make_sig(artist_name, title, year)
                if sig in seen:
                    continue

                uid = next_uid(rows)
                folder = art_dir / artist_folder(artist_name)
                folder.mkdir(parents=True, exist_ok=True)
                fn = f"{uid}__{slug(artist_name)[:60]}__{slug(title)[:90]}{('__'+slug(year)) if year else ''}.jpg"
                path = folder / fn

                try:
                    with requests.get(url, headers=UA, timeout=90, stream=True) as rr:
                        rr.raise_for_status()
                        with open(path, "wb") as f:
                            for chunk in rr.iter_content(8192):
                                if not chunk: continue
                                f.write(chunk)
                except Exception as e:
                    print("[warn] download failed:", e)
                    if path.exists(): 
                        try: path.unlink()
                        except: pass
                    continue

                rel = path.relative_to(images_root).as_posix()
                rows.append({
                    "uid": uid, "filename": rel, "artist": artist_name,
                    "title": title, "year": year, "source": "COMMONS", "license": lic, "movement": "", "keywords": ""
                })
                seen.add(sig); saved += 1
                print(f"[saved] {uid} — {artist_name} — {title}")
                time.sleep(0.1)

            cont = (data.get("continue") or {}).get("gcmcontinue")
            if not cont: break

        # Subkategorien einreihen
        subc = get_json({
            "action":"query","format":"json","formatversion":2,
            "list":"categorymembers","cmtitle":cat,
            "cmnamespace":14,"cmtype":"subcat","cmlimit":200
        })
        for cm in (subc.get("query") or {}).get("categorymembers", []):
            t = cm.get("title")
            if t and t not in visited: queue.append(t)

    write_rows(csv_path, rows); regenerate_tex(tex_path, rows)
    print(f"\nDone. Saved {saved} files.\nCSV: {csv_path}\nTEX: {tex_path}\nDir: {art_dir}")
# ---------- CLI ----------
def main():
    ap = argparse.ArgumentParser(description="Fetch PD/CC images for one artist from Wikimedia Commons (recursive).")
    ap.add_argument("--artist", required=True, help='z.B. "Wassily Kandinsky"')
    ap.add_argument("--limit", type=int, default=200, help="max. Zahl an Dateien")
    ap.add_argument("--images-root", type=str, default=None)
    args = ap.parse_args()

    images_root = resolve_images_root(args.images_root)
    fetch_commons_artist(args.artist, args.limit, images_root)

if __name__ == "__main__":
    main()
