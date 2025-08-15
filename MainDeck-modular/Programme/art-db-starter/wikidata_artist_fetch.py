#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Wikidata → Commons Fetcher for a single artist.
Gets all items where wdt:P170 = artist AND wdt:P18 (image) exists,
downloads via Commons (Special:FilePath), checks license, dedupes,
stores under Art/<LastName>/UID__Artist__Title__Year.jpg and updates
art_index.csv / art_index.tex.

Usage:
  python3 wikidata_artist_fetch.py --artist "Wassily Kandinsky" --limit 400
"""
import os, re, csv, time, argparse, urllib.parse
from pathlib import Path
import requests

# ---------- config ----------
DEFAULT_IMAGES_ROOT = "/Users/tim/NoteDeck/MainDeck-modular/Library/Images"
UA = {"User-Agent": "NoteDeck-WikidataFetcher/1.0 (local)"}
ALLOWED_LIC = ("public domain","cc","cc0","cc-by","cc-by-sa","pdm")

# ---------- utils ----------
def resolve_images_root(cli_root: str|None) -> Path:
    if cli_root: return Path(cli_root).expanduser().resolve()
    env = os.environ.get("ART_IMAGES_ROOT")
    return Path(env).expanduser().resolve() if env else Path(DEFAULT_IMAGES_ROOT).expanduser().resolve()

def slug(s: str) -> str:
    if s is None: s = ""
    s = re.sub(r"\s+", " ", s).strip()
    s = (s.replace("ä","ae").replace("ö","oe").replace("ü","ue")
           .replace("Ä","Ae").replace("Ö","Oe").replace("Ü","Ue").replace("ß","ss"))
    return re.sub(r"[^A-Za-z0-9]+","_",s).strip("_") or "untitled"

def artist_folder(artist: str) -> str:
    if not artist: return "Unknown"
    a = artist.split(";")[0]
    a = re.sub(r"\(.*?\)", "", a).strip()
    if a.lower() in {"unknown","anonymous","unidentified","unknown maker",""}:
        return "Unknown"
    last = a.split(",")[0].strip() if "," in a else (a.split() or ["Unknown"])[-1]
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

def make_sig(artist, title, year):
    norm = lambda s: slug(str(s)).lower()
    return (norm(artist), norm(title), norm(year))

def load_seen(csv_path: Path):
    return { make_sig(r["artist"], r["title"], r["year"]) for r in read_rows(csv_path) }

def retry_get(url, params=None, headers=None, timeout=30, retries=3, sleep=0.8, stream=False):
    for i in range(retries):
        try:
            r = requests.get(url, params=params, headers=headers, timeout=timeout, stream=stream)
            r.raise_for_status()
            return r
        except Exception:
            if i == retries-1: raise
            time.sleep(sleep)

# ---------- Wikidata helpers ----------
def resolve_artist_qid(name: str) -> tuple[str,str]:
    """Return (QID, label) via wbsearchentities."""
    r = retry_get("https://www.wikidata.org/w/api.php", {
        "action":"wbsearchentities","format":"json","language":"en",
        "search": name, "type":"item", "limit": 1
    }, UA).json()
    hits = r.get("search") or []
    if not hits: raise SystemExit(f"Künstler nicht gefunden: {name}")
    qid = hits[0]["id"]; label = hits[0].get("label", name)
    return qid, label

def sparql(query: str):
    r = retry_get("https://query.wikidata.org/sparql",
                  params={"query": query, "format":"json"}, headers=UA, timeout=60)
    return r.json()

def wikidata_fetch_items(artist_qid: str, limit: int):
    # Alle Werke, die das Bild P18 besitzen; inkl. Titel-Label und Jahr (P571)
    q = f"""
SELECT ?item ?itemLabel ?img ?inception WHERE {{
  ?item wdt:P170 wd:{artist_qid} .
  ?item wdt:P18 ?img .
  OPTIONAL {{ ?item wdt:P571 ?inception . }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en,de,fr,ru,es". }}
}}
LIMIT {limit}
"""
    data = sparql(q)
    rows = []
    for b in (data.get("results",{}).get("bindings") or []):
        img = b.get("img",{}).get("value","")
        label = b.get("itemLabel",{}).get("value","Untitled")
        year = ""
        if "inception" in b:
            # b['inception']['value'] is xsd:dateTime; extract year
            m = re.match(r"^(\d{4})", b["inception"]["value"])
            if m: year = m.group(1)
        rows.append((label, img, year))
    return rows

def commons_license_and_direct_url(file_title_no_prefix: str):
    """Return (license_short, direct_url) using Commons API extmetadata."""
    title = "File:" + file_title_no_prefix
    r = retry_get("https://commons.wikimedia.org/w/api.php", {
        "action":"query","format":"json","formatversion":2,
        "titles": title,
        "prop":"imageinfo",
        "iiprop":"url|mime|size|extmetadata",
        "iiextmetadatafilter":"LicenseShortName|Artist|ObjectName|Date",
        "iiurlwidth":4096
    }, UA, timeout=40).json()
    pages = (r.get("query") or {}).get("pages") or []
    if not pages: return ("", "")
    ii = (pages[0].get("imageinfo") or [{}])[0]
    meta = ii.get("extmetadata") or {}
    lic = (meta.get("LicenseShortName",{}).get("value","") or "").lower()
    url = ii.get("url") or ii.get("thumburl") or ""
    return lic, url

# ---------- core ----------
def fetch_artist(name: str, limit: int, images_root: Path):
    art_dir = images_root / "Art"; art_dir.mkdir(parents=True, exist_ok=True)
    csv_path = art_dir / "art_index.csv"
    tex_path = art_dir / "art_index.tex"
    ensure_index(csv_path)

    rows = read_rows(csv_path)
    seen = load_seen(csv_path)

    qid, label = resolve_artist_qid(name)
    print(f"[wikidata] {name} → {qid} ({label})")
    items = wikidata_fetch_items(qid, limit*2)  # überziehen etwas, manche fallen wegen Lizenz raus
    print(f"[wikidata] candidate items with images:", len(items))

    saved = 0
    for title, img_iri, year in items:
        if saved >= limit: break
        # img_iri ist i. d. R. .../Special:FilePath/<filename>
        file_part = img_iri.split("/Special:FilePath/")[-1]
        file_part = urllib.parse.unquote(file_part)
        lic, direct = commons_license_and_direct_url(file_part)
        if not direct: 
            continue
        if not any(k in lic for k in ALLOWED_LIC):
            continue

        sig = make_sig(name, title, year)
        if sig in seen:
            continue

        uid = next_uid(rows)
        folder = art_dir / artist_folder(name)
        folder.mkdir(parents=True, exist_ok=True)
        fn = f"{uid}__{slug(name)[:60]}__{slug(title)[:90]}{('__'+slug(year)) if year else ''}{Path(direct).suffix or '.jpg'}"
        path = folder / fn

        try:
            with retry_get(direct, headers=UA, timeout=90, retries=3, stream=True) as rr:
                with open(path, "wb") as f:
                    for chunk in rr.iter_content(8192):
                        if chunk: f.write(chunk)
        except Exception as e:
            print("[warn] download failed:", e); 
            try: path.unlink()
            except: pass
            continue

        rel = path.relative_to(images_root).as_posix()
        rows.append({
            "uid": uid, "filename": rel, "artist": name,
            "title": title, "year": year, "source": "WIKIDATA+COMMONS", "license": lic, "movement": "", "keywords": ""
        })
        write_rows(csv_path, rows); regenerate_tex(tex_path, rows)  # inkrementell, falls Crash
        seen.add(sig); saved += 1
        print(f"[saved] {uid} — {name} — {title} ({year})")
        time.sleep(0.15)

    regenerate_tex(tex_path, rows)
    print(f"\nDone. Saved {saved} files.\nCSV: {csv_path}\nTEX: {tex_path}\nDir: {art_dir}")

# ---------- CLI ----------
def main():
    ap = argparse.ArgumentParser(description="Fetch artist images via Wikidata (P18) + Commons.")
    ap.add_argument("--artist", required=True, help='z.B. "Wassily Kandinsky"')
    ap.add_argument("--limit", type=int, default=300)
    ap.add_argument("--images-root", type=str, default=None)
    args = ap.parse_args()
    images_root = resolve_images_root(args.images_root)
    fetch_artist(args.artist, args.limit, images_root)

if __name__ == "__main__":
    main()
