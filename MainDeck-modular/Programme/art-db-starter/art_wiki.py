#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Wikidata → Commons Fetcher für Künstler / Werk + flacher Galerie-Builder.
Jetzt zusätzlich:
- --commons-category <CategoryName>
- Qualitätsfilter: --min-width/--min-height (Default 2000)
- Dublettencheck via perceptual hash (imagehash, Hamming-Distanz ≤ 5 => skip)
"""
import os, re, csv, time, argparse, urllib.parse, itertools, json
from pathlib import Path
import requests
from PIL import Image
import imagehash

# ---------- config ----------
DEFAULT_IMAGES_ROOT = "/Users/tim/NoteDeck/MainDeck-modular/Library/Images"
UA = {"User-Agent": "NoteDeck-WikidataFetcher/1.3 (local)"}
ALLOWED_LIC = ("public domain","cc","cc0","cc-by","cc-by-sa","pdm")

CSV_NAME = "art_index.csv"
GALLERY_TEX = "art_gallery.tex"
HASH_INDEX = "hash_index.json"
PHASH_DISTANCE_MAX = 3  # <=5 gilt als Dublette/zu ähnlich

# ---------- utils ----------
import re

def artist_from_category(cat: str) -> str:
    """Leite aus einer Commons-Kategorie den Künstlernamen ab."""
    # z.B. "Paintings_by_Hilma_af_Klint" -> "Hilma af Klint"
    m = re.match(r"^(?:Paintings|Works|Artworks|Drawings|Photographs|Sculptures)_by_(.+)$", cat)
    if m:
        return m.group(1).replace("_", " ")
    # z.B. "Hilma_af_Klint" -> "Hilma af Klint"
    return cat.replace("_", " ")



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

def _tex_esc(s: str) -> str:
    return (s or "").replace("\\","\\textbackslash{}") \
                    .replace("{","\\{").replace("}","\\}") \
                    .replace("#","\\#").replace("%","\\%") \
                    .replace("&","\\&").replace("_","\\_") \
                    .replace("^","\\^{}").replace("~","\\~{}")

def make_sig(artist, title, year):
    norm = lambda s: slug(str(s)).lower()
    return (norm(artist), norm(title), norm(year))

def load_seen(csv_path: Path):
    return { make_sig(r["artist"], r["title"], r["year"]) for r in read_rows(csv_path) }

def sort_rows(rows, mode: str):
    mode = (mode or "uid").lower()
    if mode == "artist":
        return sorted(rows, key=lambda r: (r["artist"].lower(), r["year"] or "", r["title"].lower(), r["uid"]))
    if mode == "year":
        def year_key(r):
            y = r["year"]
            try: yi = int(y)
            except: yi = 10**9
            return (yi, r["artist"].lower(), r["title"].lower())
        return sorted(rows, key=year_key)
    if mode == "title":
        return sorted(rows, key=lambda r: (r["title"].lower(), r["artist"].lower(), r["uid"]))
    def uid_num(r):
        m = re.match(r"ART(\d+)$", r.get("uid","ART0"))
        return int(m.group(1)) if m else 0
    return sorted(rows, key=uid_num)

# ---------- image helpers ----------
def convert_tiff_to_jpg(src_path: Path) -> Path:
    dst_path = src_path.with_suffix(".jpg")
    with Image.open(src_path) as im:
        if im.mode not in ("RGB", "L"):
            im = im.convert("RGB")
        im.save(dst_path, "JPEG", quality=90, optimize=True, progressive=True)
    try: src_path.unlink()
    except: pass
    return dst_path

def compute_phash(path: Path) -> imagehash.ImageHash:
    with Image.open(path) as im:
        return imagehash.phash(im)

def load_hash_index(art_dir: Path) -> dict:
    hp = art_dir / HASH_INDEX
    if hp.exists():
        try:
            return json.loads(hp.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}

def save_hash_index(art_dir: Path, idx: dict):
    (art_dir / HASH_INDEX).write_text(json.dumps(idx, ensure_ascii=False, indent=2), encoding="utf-8")

def is_similar_hash(new_hash: imagehash.ImageHash, existing_hex_list: list[str], max_dist: int = PHASH_DISTANCE_MAX) -> bool:
    for hx in existing_hex_list:
        try:
            if new_hash - imagehash.hex_to_hash(hx) <= max_dist:
                return True
        except Exception:
            continue
    return False

# ---------- gallery ----------
def regenerate_gallery(gallery_tex: Path, rows, per_page: int = 6, sort_mode: str = "uid",
                       title: str = "Art Gallery", standalone: bool = False,
                       images_root_texpath: str = "/Users/tim/NoteDeck/MainDeck-modular/Library/Images/"):
    groups = {}
    for r in rows:
        groups.setdefault(r["artist"], []).append(r)
    artists = sorted(groups.keys(), key=lambda a: a.lower())

    lines = []
    if standalone:
        lines += [
            r"\documentclass[11pt]{article}",
            r"\usepackage[margin=2.5cm]{geometry}",
            r"\usepackage{graphicx}",
            r"\usepackage[T1]{fontenc}",
            r"\usepackage[utf8]{inputenc}",
            r"\usepackage{microtype}",
            r"\usepackage{babel}",
            rf"\graphicspath{{{{{images_root_texpath}}}}}",
            r"\setlength{\parindent}{0pt}",
            r"\raggedbottom",
            rf"\title{{{_tex_esc(title)}}}",
            r"\date{}",
            r"\begin{document}",
            r"\maketitle",
            ""
        ]

    lines += [
        r"% Auto-generated — DO NOT EDIT.",
        "",
        r"% Nur Dateiname (ohne Pfad) aus einem Pfad ziehen",
        r"\makeatletter",
        r"\newcommand{\basename}[1]{\begingroup\filename@parse{#1}\filename@base\filename@ext\endgroup}",
        r"\makeatother",
        "",
        r"% Einzeilige Codezeile (monospace), skaliert auf \linewidth",
        r"\newcommand{\ArtCodeLine}[1]{\par\noindent{\scriptsize\ttfamily \resizebox{\linewidth}{!}{#1}}}",
        r"",
        r"% Robuste Kachel: rendert nichts, wenn Pfad leer ist",
        r"\newcommand{\ArtTile}[2]{% #1=path, #2=caption",
        r"  \begin{minipage}[t]{0.48\textwidth}",
        r"    \centering",
        r"    \if\relax\detokenize{#1}\relax",
        r"      % leer",
        r"    \else",
        r"      \includegraphics[width=\linewidth,height=0.28\textheight,keepaspectratio]{#1}\\[0.6ex]",
        r"      {\footnotesize\itshape #2}\\[-0.2ex]",
        r"      \ArtCodeLine{\basename{#1}}",
        r"    \fi",
        r"  \end{minipage}}",
        r"",
        r"\newcommand{\ArtRow}[4]{% #1..#4 = (path,caption) links/rechts",
        r"  \noindent\ArtTile{#1}{#2}\hfill\ArtTile{#3}{#4}\par\vspace{1.0em}}",
        r"",
        rf"\section*{{{_tex_esc(title)}}}",
        ""
    ]

    def row_two(cells):
        left  = cells[0] if len(cells) > 0 else ("","")
        right = cells[1] if len(cells) > 1 else ("","")
        def esc_pair(pc):
            p, c = pc
            return (_tex_esc(p), _tex_esc(c))
        (p1, c1) = esc_pair(left); (p2, c2) = esc_pair(right)
        return fr"\ArtRow{{{p1}}}{{{c1}}}{{{p2}}}{{{c2}}}"

    for artist in artists:
        group = sort_rows(groups[artist], sort_mode)
        lines.append(fr"\section*{{{_tex_esc(artist)}}}")
        buf = []
        for r in group:
            cap = f"{r['artist']}, {r['title']}" + (f" ({r['year']})" if r['year'] else "")
            buf.append((r["filename"], cap))
            if len(buf) == 2:
                lines.append(row_two(buf)); lines.append("")
                buf = []
        if buf:
            p1, c1 = _tex_esc(buf[0][0]), _tex_esc(buf[0][1])
            lines.append(fr"\noindent\ArtTile{{{p1}}}{{{c1}}}\par\vspace{{1.0em}}")
            lines.append("")

    if standalone:
        lines.append(r"\end{document}")

    gallery_tex.write_text("\n".join(lines), encoding="utf-8")

# ---------- HTTP helpers ----------
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
            m = re.match(r"^(\d{4})", b["inception"]["value"])
            if m: year = m.group(1)
        rows.append((label, img, year))
    return rows

def wikidata_fetch_work_items(title_query: str, artist_qid: str | None = None, limit: int = 10):
    def wbsearch_ids(title: str, lang: str, n: int = 50):
        r = retry_get("https://www.wikidata.org/w/api.php", {
            "action":"wbsearchentities","format":"json","language":lang,
            "search": title, "type":"item", "limit": n
        }, UA, timeout=40).json()
        return [hit["id"] for hit in (r.get("search") or []) if "id" in hit]

    qids = []
    for lang in ("en","de","fr"):
        qids = wbsearch_ids(title_query, lang)
        if qids: break

    sr = f'{title_query} haswbstatement:P170={artist_qid}' if artist_qid else title_query
    r = retry_get("https://www.wikidata.org/w/api.php", {
        "action":"query","list":"search","format":"json",
        "srsearch": sr, "srlimit": 50, "srnamespace": 0
    }, UA, timeout=40).json()
    for hit in (r.get("query",{}).get("search") or []):
        t = hit.get("title","")
        if t.startswith("Q") and t[1:].isdigit():
            qids.append(t)

    qids = list(dict.fromkeys(qids))

    results = []
    def batch_via_qids(qids_batch):
        nonlocal results
        if not qids_batch: return
        values = " ".join(f"wd:{qid}" for qid in qids_batch)
        artist_filter = f"  ?item wdt:P170 wd:{artist_qid} .\n" if artist_qid else ""
        q = f"""
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
SELECT ?item ?itemLabel ?img ?inception WHERE {{
  VALUES ?item {{ {values} }}
{artist_filter}
  ?item wdt:P18 ?img .
  OPTIONAL {{ ?item wdt:P571 ?inception . }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en,de,fr,ru,es". }}
}}
"""
        data = sparql(q)
        for b in (data.get("results",{}).get("bindings") or []):
            img = b.get("img",{}).get("value","")
            if not img: continue
            label = b.get("itemLabel",{}).get("value","Untitled")
            year = ""
            if "inception" in b:
                m = re.match(r"^(\d{4})", b["inception"]["value"])
                if m: year = m.group(1)
            results.append((label, img, year))

    if qids:
        batch_via_qids(qids[:80])

    if not results:
        t = title_query.replace('"', '\\"')
        artist_filter = f"  ?item wdt:P170 wd:{artist_qid} .\n" if artist_qid else ""
        q = f"""
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
SELECT ?item ?itemLabel ?img ?inception WHERE {{
  ?item wdt:P18 ?img .
{artist_filter}
  FILTER (
    EXISTS {{ ?item rdfs:label ?lbl . FILTER(CONTAINS(LCASE(STR(?lbl)), LCASE("{t}"))) }} ||
    EXISTS {{ ?item skos:altLabel ?albl . FILTER(CONTAINS(LCASE(STR(?albl)), LCASE("{t}"))) }}
  )
  OPTIONAL {{ ?item wdt:P571 ?inception . }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en,de,fr,ru,es". }}
}}
LIMIT {max(50, limit*5)}
"""
        data = sparql(q)
        for b in (data.get("results",{}).get("bindings") or []):
            img = b.get("img",{}).get("value","")
            if not img: continue
            label = b.get("itemLabel",{}).get("value","Untitled")
            year = ""
            if "inception" in b:
                m = re.match(r"^(\d{4})", b["inception"]["value"])
                if m: year = m.group(1)
            results.append((label, img, year))

    out, seen = [], set()
    for tup in results:
        if tup in seen: continue
        seen.add(tup); out.append(tup)
        if len(out) >= limit: break
    return out

# ---------- Commons helpers ----------
def commons_license_and_direct_url(file_title_no_prefix: str):
    """Returns (license, url, mime, width, height)."""
    title = "File:" + file_title_no_prefix
    r = retry_get("https://commons.wikimedia.org/w/api.php", {
        "action":"query","format":"json","formatversion":2,
        "titles": title,
        "prop":"imageinfo",
        "iiprop":"url|mime|size|extmetadata|thumburl",
        "iiextmetadatafilter":"LicenseShortName|Artist|ObjectName|Date",
        "iiurlwidth":4096
    }, UA, timeout=40).json()
    pages = (r.get("query") or {}).get("pages") or []
    if not pages: return ("", "", "", 0, 0)
    ii = (pages[0].get("imageinfo") or [{}])[0]
    meta = ii.get("extmetadata") or {}
    lic = (meta.get("LicenseShortName",{}).get("value","") or "").lower()
    mime = (ii.get("mime") or "").lower()
    url = ii.get("url") or ii.get("thumburl") or ""
    width = int(ii.get("width") or 0)
    height = int(ii.get("height") or 0)
    return lic, url, mime, width, height

# ---------- core ----------
def fetch_artist(name: str, limit: int, images_root: Path,
                 per_page: int, sort_mode: str,
                 standalone: bool, images_root_texpath: str,
                 min_width: int, min_height: int):
    art_dir = images_root / "Art"
    art_dir.mkdir(parents=True, exist_ok=True)
    csv_path = art_dir / CSV_NAME
    gallery_path = art_dir / GALLERY_TEX
    hash_idx = load_hash_index(art_dir)

    ensure_index(csv_path)
    rows = read_rows(csv_path)
    seen = load_seen(csv_path)

    qid, label = resolve_artist_qid(name)
    print(f"[wikidata] {name} → {qid} ({label})")
    items = wikidata_fetch_items(qid, limit*2)
    print(f"[wikidata] candidate items with images:", len(items))

    saved = 0
    for title, img_iri, year in items:
        if saved >= limit: break
        file_part = urllib.parse.unquote(img_iri.split("/Special:FilePath/")[-1])
        lic, direct, mime, width, height = commons_license_and_direct_url(file_part)
        if not direct or not any(k in lic for k in ALLOWED_LIC):
            continue
        if width < min_width or height < min_height:
            continue

        sig = make_sig(name, title, year)
        if sig in seen:
            continue

        uid = next_uid(rows)
        ext = Path(urllib.parse.urlparse(direct).path).suffix or ".jpg"
        fn = f"{uid}__{slug(name)[:60]}__{slug(title)[:90]}{('__'+slug(year)) if year else ''}{ext}"
        path = (images_root / "Art" / fn)

        try:
            with retry_get(direct, headers=UA, timeout=90, retries=3, stream=True) as rr:
                with open(path, "wb") as f:
                    for chunk in rr.iter_content(8192):
                        if chunk: f.write(chunk)
            if mime in ("image/tif", "image/tiff"):
                print("[convert] TIFF → JPG:", path.name)
                path = convert_tiff_to_jpg(path)

            # Dublettencheck via perceptual hash
            ph = compute_phash(path)
            if is_similar_hash(ph, list(hash_idx.values())):
                print("[skip] duplicate (phash):", path.name)
                try: path.unlink()
                except: pass
                continue

        except Exception as e:
            print("[warn] download/convert failed:", e)
            try: path.unlink()
            except: pass
            continue

        rel = path.relative_to(images_root).as_posix()
        rows.append({
            "uid": uid, "filename": rel, "artist": name,
            "title": title, "year": year, "source": "WIKIDATA+COMMONS", "license": lic,
            "movement": "", "keywords": ""
        })
        write_rows(csv_path, rows)
        hash_idx[uid] = ph.__str__()  # hex
        save_hash_index(art_dir, hash_idx)

        regenerate_gallery(gallery_path, rows, per_page=per_page, sort_mode=sort_mode,
                           title="Art Gallery", standalone=standalone, images_root_texpath=images_root_texpath)
        seen.add(sig); saved += 1
        print(f"[saved] {uid} — {name} — {title} ({year})")
        time.sleep(0.1)

    regenerate_gallery(gallery_path, rows, per_page=per_page, sort_mode=sort_mode,
                       title="Art Gallery", standalone=standalone, images_root_texpath=images_root_texpath)
    print(f"\nDone. Saved {saved} files."
          f"\nCSV: {csv_path}\nGALLERY: {gallery_path}\nDir: {art_dir}")

def fetch_work(work_title: str, work_artist_name: str | None, limit: int, images_root: Path,
               per_page: int, sort_mode: str, standalone: bool, images_root_texpath: str,
               min_width: int, min_height: int):
    art_dir = images_root / "Art"
    art_dir.mkdir(parents=True, exist_ok=True)
    csv_path = art_dir / CSV_NAME
    gallery_path = art_dir / GALLERY_TEX
    hash_idx = load_hash_index(art_dir)

    ensure_index(csv_path)
    rows = read_rows(csv_path)
    seen = load_seen(csv_path)

    artist_qid = None
    artist_label = ""
    if work_artist_name:
        artist_qid, artist_label = resolve_artist_qid(work_artist_name)

    print(f"[wikidata] work search: {work_title}" + (f" (artist: {work_artist_name} → {artist_qid})" if artist_qid else ""))
    items = wikidata_fetch_work_items(work_title, artist_qid=artist_qid, limit=max(3, limit*2))
    print(f"[wikidata] candidate works with images:", len(items))

    saved = 0
    for title, img_iri, year in items:
        if saved >= limit: break
        file_part = urllib.parse.unquote(img_iri.split("/Special:FilePath/")[-1])
        lic, direct, mime, width, height = commons_license_and_direct_url(file_part)
        if not direct or not any(k in lic for k in ALLOWED_LIC):
            continue
        if width < min_width or height < min_height:
            continue

        artist_for_sig = work_artist_name or artist_label or ""
        sig = make_sig(artist_for_sig, title, year)
        if sig in seen:
            print("[skip] already seen:", sig); continue

        uid = next_uid(rows)
        ext = Path(urllib.parse.urlparse(direct).path).suffix or ".jpg"
        artist_slug = slug(artist_for_sig)[:60] if artist_for_sig else "unknown_artist"
        fn = f"{uid}__{artist_slug}__{slug(title)[:90]}{('__'+slug(year)) if year else ''}{ext}"
        path = (images_root / "Art" / fn)

        try:
            with retry_get(direct, headers=UA, timeout=90, retries=3, stream=True) as rr:
                with open(path, "wb") as f:
                    for chunk in rr.iter_content(8192):
                        if chunk: f.write(chunk)
            if mime in ("image/tif", "image/tiff"):
                print("[convert] TIFF → JPG:", path.name)
                path = convert_tiff_to_jpg(path)

            ph = compute_phash(path)
            if is_similar_hash(ph, list(hash_idx.values())):
                print("[skip] duplicate (phash):", path.name)
                try: path.unlink()
                except: pass
                continue

        except Exception as e:
            print("[warn] download/convert failed:", e)
            try: path.unlink()
            except: pass
            continue

        rel = path.relative_to(images_root).as_posix()
        rows.append({
            "uid": uid, "filename": rel,
            "artist": artist_for_sig or "", "title": title, "year": year,
            "source": "WIKIDATA+COMMONS", "license": lic,
            "movement": "", "keywords": ""
        })
        write_rows(csv_path, rows)
        hash_idx[uid] = ph.__str__()
        save_hash_index(art_dir, hash_idx)

        regenerate_gallery(gallery_path, rows, per_page=per_page, sort_mode=sort_mode,
                           title="Art Gallery", standalone=standalone, images_root_texpath=images_root_texpath)
        seen.add(sig); saved += 1
        print(f"[saved] {uid} — {artist_for_sig} — {title} ({year})")
        time.sleep(0.1)

    regenerate_gallery(gallery_path, rows, per_page=per_page, sort_mode=sort_mode,
                       title="Art Gallery", standalone=standalone, images_root_texpath=images_root_texpath)
    print(f"\nDone (work mode). Saved {saved} files."
          f"\nCSV: {csv_path}\nGALLERY: {gallery_path}\nDir: {art_dir}")

def fetch_commons_file(file_title_no_prefix: str, artist_hint: str | None, images_root: Path,
                       per_page: int, sort_mode: str, standalone: bool, images_root_texpath: str,
                       min_width: int, min_height: int):
    art_dir = images_root / "Art"
    art_dir.mkdir(parents=True, exist_ok=True)
    csv_path = art_dir / CSV_NAME
    gallery_path = art_dir / GALLERY_TEX
    hash_idx = load_hash_index(art_dir)

    ensure_index(csv_path)
    rows = read_rows(csv_path)
    seen = load_seen(csv_path)

    lic, direct, mime, width, height = commons_license_and_direct_url(file_title_no_prefix)
    if not direct:
        raise SystemExit(f"Commons-Datei nicht gefunden: {file_title_no_prefix}")
    if not any(k in lic for k in ALLOWED_LIC):
        raise SystemExit(f"Nicht erlaubte Lizenz: {lic}")
    if width < min_width or height < min_height:
        raise SystemExit(f"Zu geringe Auflösung: {width}x{height} (min {min_width}x{min_height})")

    base = Path(file_title_no_prefix).stem.replace("_"," ").strip()
    title_guess = base
    year_guess = ""

    sig = make_sig(artist_hint or "", title_guess, year_guess)
    if sig in seen:
        print("[skip] already in index:", sig)
    else:
        rows = read_rows(csv_path)
        uid = next_uid(rows)
        ext = Path(urllib.parse.urlparse(direct).path).suffix or ".jpg"
        artist_slug = slug(artist_hint)[:60] if artist_hint else "unknown_artist"
        fn = f"{uid}__{artist_slug}__{slug(title_guess)[:90]}{ext}"
        path = (images_root / "Art" / fn)

        try:
            with retry_get(direct, headers=UA, timeout=90, retries=3, stream=True) as rr:
                with open(path, "wb") as f:
                    for chunk in rr.iter_content(8192):
                        if chunk: f.write(chunk)
            if mime in ("image/tif", "image/tiff"):
                print("[convert] TIFF → JPG:", path.name)
                path = convert_tiff_to_jpg(path)

            ph = compute_phash(path)
            if is_similar_hash(ph, list(hash_idx.values())):
                print("[skip] duplicate (phash):", path.name)
                try: path.unlink()
                except: pass
                return

        except Exception as e:
            print("[warn] download/convert failed:", e)
            try: path.unlink()
            except: pass
            raise

        rel = path.relative_to(images_root).as_posix()
        rows.append({
            "uid": uid, "filename": rel,
            "artist": artist_hint or "", "title": title_guess, "year": year_guess,
            "source": "COMMONS", "license": lic,
            "movement": "", "keywords": ""
        })
        write_rows(csv_path, rows)
        hash_idx[uid] = ph.__str__()
        save_hash_index(art_dir, hash_idx)

    regenerate_gallery(gallery_path, read_rows(csv_path), per_page=per_page, sort_mode=sort_mode,
                       title="Art Gallery", standalone=standalone, images_root_texpath=images_root_texpath)
    print("Done (commons file).")

def fetch_commons_category(category: str, limit: int, images_root: Path,
                           per_page: int, sort_mode: str, standalone: bool, images_root_texpath: str,
                           min_width: int, min_height: int):
    """
    Ziehe Dateien direkt aus einer Commons-Kategorie (ohne Wikidata-Zwang).
    Kategorie OHNE 'Category:'-Präfix übergeben, z. B. 'Hilma_af_Klint' oder 'Paintings_by_Hilma_af_Klint'.
    """
    art_dir = images_root / "Art"
    art_dir.mkdir(parents=True, exist_ok=True)
    csv_path = art_dir / CSV_NAME
    gallery_path = art_dir / GALLERY_TEX
    hash_idx = load_hash_index(art_dir)

    ensure_index(csv_path)
    rows = read_rows(csv_path)
    seen = load_seen(csv_path)

    saved = 0
    cmcontinue = None
    while saved < limit:
        params = {
            "action": "query", "format": "json",
            "list": "categorymembers",
            "cmtitle": f"Category:{category}",
            "cmtype": "file",
            "cmlimit": 50,
        }
        if cmcontinue: params["cmcontinue"] = cmcontinue

        r = retry_get("https://commons.wikimedia.org/w/api.php", params, UA, timeout=40).json()
        members = (r.get("query", {}).get("categorymembers") or [])
        if not members:
            break

        for m in members:
            if saved >= limit: break
            title = m.get("title","")
            if not title.startswith("File:"): continue
            file_title_no_prefix = title.split("File:",1)[1]

            lic, direct, mime, width, height = commons_license_and_direct_url(file_title_no_prefix)
            if not direct or not any(k in lic for k in ALLOWED_LIC):
                continue
            if width < min_width or height < min_height:
                continue

            # 'artist' notfalls aus Kategorienamen ableiten
            artist_name = artist_from_category(category)
            base = Path(file_title_no_prefix).stem.replace("_"," ").strip()
            title_guess = base
            year_guess = ""

            sig = make_sig(artist_name, title_guess, year_guess)
            if sig in seen:
                continue

            uid = next_uid(rows)
            ext = Path(urllib.parse.urlparse(direct).path).suffix or ".jpg"
            fn = f"{uid}__{slug(artist_name)[:60]}__{slug(title_guess)[:90]}{ext}"
            path = (images_root / "Art" / fn)

            try:
                with retry_get(direct, headers=UA, timeout=90, retries=3, stream=True) as rr:
                    with open(path, "wb") as f:
                        for chunk in rr.iter_content(8192):
                            if chunk: f.write(chunk)
                if mime in ("image/tif", "image/tiff"):
                    print("[convert] TIFF → JPG:", path.name)
                    path = convert_tiff_to_jpg(path)

                ph = compute_phash(path)
                if is_similar_hash(ph, list(hash_idx.values())):
                    print("[skip] duplicate (phash):", path.name)
                    try: path.unlink()
                    except: pass
                    continue

            except Exception as e:
                print("[warn] download/convert failed:", e)
                try: path.unlink()
                except: pass
                continue

            rel = path.relative_to(images_root).as_posix()
            rows.append({
                "uid": uid, "filename": rel,
                "artist": artist_name, "title": title_guess, "year": year_guess,
                "source": "COMMONS_CATEGORY", "license": lic,
                "movement": "", "keywords": ""
            })
            write_rows(csv_path, rows)
            hash_idx[uid] = ph.__str__()
            save_hash_index(art_dir, hash_idx)

            regenerate_gallery(gallery_path, rows, per_page=per_page, sort_mode=sort_mode,
                               title="Art Gallery", standalone=standalone, images_root_texpath=images_root_texpath)
            seen.add(sig); saved += 1
            print(f"[saved] {uid} — {artist_name} — {title_guess}")

        cmcontinue = (r.get("continue") or {}).get("cmcontinue")
        if not cmcontinue:
            break

    regenerate_gallery(gallery_path, rows, per_page=per_page, sort_mode=sort_mode,
                       title="Art Gallery", standalone=standalone, images_root_texpath=images_root_texpath)
    print(f"\nDone (commons category). Saved {saved} files."
          f"\nCSV: {csv_path}\nGALLERY: {gallery_path}\nDir: {art_dir}")

# ---------- CLI ----------
def main():
    ap = argparse.ArgumentParser(description="Fetch artist/work images via Wikidata (P18) + Commons; flat gallery builder.")
    ap.add_argument("--artist", help='z.B. "Wassily Kandinsky"')
    ap.add_argument("--work", type=str, help='Werk-/Titel-Suche, z.B. "Intersecting Lines"')
    ap.add_argument("--work-artist", type=str, help='(Optional) Künstlername zur Eingrenzung, z.B. "Wassily Kandinsky"')
    ap.add_argument("--commons-file", type=str, help='Direkter Commons-Dateiname, z.B. "Intersecting_Lines_by_Wassily_Kandinsky.jpg"')
    ap.add_argument("--commons-category", type=str, help='Commons-Kategorie (ohne "Category:"), z. B. "Hilma_af_Klint"')

    ap.add_argument("--limit", type=int, default=300)
    ap.add_argument("--images-root", type=str, default=None)
    ap.add_argument("--rebuild-only", action="store_true", help="Nur art_gallery.tex aus CSV neu erzeugen")
    ap.add_argument("--per-page", type=int, default=6, help="Bilder pro Seite (Standard 6 = 3x2)")
    ap.add_argument("--sort", type=str, default="uid", choices=["uid","artist","year","title"], help="Sortierung für die Galerie")
    ap.add_argument("--standalone", action="store_true", help="art_gallery.tex als eigenständiges LaTeX-Dokument mit Header erzeugen")
    ap.add_argument("--image-root-texpath", type=str,
                    default="/Users/tim/NoteDeck/MainDeck-modular/Library/Images/",
                    help="Pfad für \\graphicspath im Standalone-Modus")
    ap.add_argument("--min-width", type=int, default=2000, help="Mindestbreite für Bilder")
    ap.add_argument("--min-height", type=int, default=2000, help="Mindesthöhe für Bilder")
    args = ap.parse_args()

    images_root = resolve_images_root(args.images_root)
    art_dir = images_root / "Art"
    csv_path = art_dir / CSV_NAME
    gallery_path = art_dir / GALLERY_TEX

    if args.rebuild_only:
        rows = read_rows(csv_path)
        regenerate_gallery(
            gallery_path, rows, per_page=args.per_page, sort_mode=args.sort, title="Art Gallery",
            standalone=args.standalone, images_root_texpath=args.image_root_texpath
        )
        print(f"Gallery rebuilt.\nCSV: {csv_path}\nGALLERY: {gallery_path}")
        return

    if args.commons_category:
        fetch_commons_category(
            args.commons_category, args.limit, images_root,
            per_page=args.per_page, sort_mode=args.sort, standalone=args.standalone,
            images_root_texpath=args.image_root_texpath,
            min_width=args.min_width, min_height=args.min_height
        )
        return

    if args.commons_file:
        fetch_commons_file(
            args.commons_file, args.work_artist, images_root,
            per_page=args.per_page, sort_mode=args.sort,
            standalone=args.standalone, images_root_texpath=args.image_root_texpath,
            min_width=args.min_width, min_height=args.min_height
        )
        return

    if args.work:
        fetch_work(
            args.work, args.work_artist, args.limit, images_root,
            per_page=args.per_page, sort_mode=args.sort,
            standalone=args.standalone, images_root_texpath=args.image_root_texpath,
            min_width=args.min_width, min_height=args.min_height
        )
        return

    if not args.artist:
        raise SystemExit("Fehler: --artist ist erforderlich (oder --work / --commons-file / --commons-category / --rebuild-only verwenden).")

    fetch_artist(
        args.artist, args.limit, images_root,
        per_page=args.per_page, sort_mode=args.sort,
        standalone=args.standalone, images_root_texpath=args.image_root_texpath,
        min_width=args.min_width, min_height=args.min_height
    )

if __name__ == "__main__":
    main()
