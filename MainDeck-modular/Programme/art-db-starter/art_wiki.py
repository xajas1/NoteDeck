#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
Wikidata → Commons Fetcher für Künstler / Werk + künstlerzentrierter Galerie-Builder.

Neu (Stand dieses Skripts):
- Standard: pro Künstler eigenständige PDF-fähige TeX mit Header (Standalone).
- Optional: Master-Datei art_gallery_master.tex, die Fragmente (ohne Header) via \input{} einbindet,
  wenn --no-artist-standalone --build-master genutzt wird.
- Rebuild-Logik erzeugt je nach Modus Standalone- oder Fragment-Galerien + optional Master.
"""
import os, re, csv, time, argparse, urllib.parse, json
from pathlib import Path
import requests
from PIL import Image
import imagehash
import sys


# ---------- config ----------
DEFAULT_IMAGES_ROOT = "/Users/tim/NoteDeck/MainDeck-modular/Library/Images"
UA = {"User-Agent": "NoteDeck-WikidataFetcher/1.5 (local)"}
ALLOWED_LIC = ("public domain","cc","cc0","cc-by","cc-by-sa","pdm")

CSV_NAME = "art_index.csv"
MASTER_GALLERY = "art_gallery_master.tex"
GALLERIES_DIR = "Galleries"
HASH_INDEX = "hash_index.json"
PHASH_DISTANCE_MAX = 1  # <=5 = zu ähnlich


def normalize_artist(a: str) -> str:
    if not a: return "Unknown Artist"
    a = a.replace("_", " ").strip()
    m = re.match(r"^(?:Paintings|Works|Artworks|Drawings|Photographs|Sculptures)\s+by\s+(.+)$", a, re.I)
    return (m.group(1) if m else a).strip()

def make_sig(artist, title, year):
    norm = lambda s: slug(str(s)).lower()
    return (norm(normalize_artist(artist)), norm(title), norm(year))


# --- neu: nearest phash helper ---
def nearest_phash_match(new_hash, hash_idx: dict):
    """Gibt (min_dist, closest_uid) zurück; dist ist Hamming-Distanz."""
    min_dist, closest_uid = 10**9, None
    for uid, hx in hash_idx.items():
        try:
            d = new_hash - imagehash.hex_to_hash(hx)
        except Exception:
            continue
        if d < min_dist:
            min_dist, closest_uid = d, uid
    return min_dist, closest_uid



# ---------- utils ----------
def artist_from_category(cat: str) -> str:
    m = re.match(r"^(?:Paintings|Works|Artworks|Drawings|Photographs|Sculptures)_by_(.+)$", cat)
    if m: return m.group(1).replace("_", " ")
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
        m = re.match(r"ART(\d+)$", (r.get("uid") or ""))
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
    return { make_sig(r.get("artist",""), r.get("title",""), r.get("year","")) for r in read_rows(csv_path) }

def sort_rows(rows, mode: str):
    mode = (mode or "uid").lower()
    if mode == "artist":
        return sorted(rows, key=lambda r: ((r.get("artist") or "").lower(),
                                           r.get("year") or "",
                                           (r.get("title") or "").lower(),
                                           r.get("uid") or ""))
    if mode == "year":
        def year_key(r):
            y = r.get("year") or ""
            m = re.match(r"^(\d{4})", str(y))
            yi = int(m.group(1)) if m else 10**9
            return (yi, (r.get("artist") or "").lower(), (r.get("title") or "").lower(), r.get("uid") or "")
        return sorted(rows, key=year_key)
    if mode == "title":
        return sorted(rows, key=lambda r: ((r.get("title") or "").lower(),
                                           (r.get("artist") or "").lower(),
                                           r.get("uid") or ""))
    def uid_num(r):
        m = re.match(r"ART(\d+)$", (r.get("uid") or "ART0"))
        return int(m.group(1)) if m else 0
    return sorted(rows, key=uid_num)

def _normalize_graphicspath(p: str) -> str:
    """LaTeX-graphicspath-kompatibel: Slashes und Slash am Ende."""
    if not p: return "/"
    p = p.replace("\\", "/")
    if not p.endswith("/"): p += "/"
    return p

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

# ---------- per-artist gallery helpers ----------
def _gallery_preamble(header: bool, title: str, images_root_texpath: str, include_macros: bool):
    r"""Erzeuge Preambel-Teile. header=True → voller Dokument-Header.
       include_macros=True → Makros (\ArtTile etc.) definieren."""
    lines = []
    if header:
        images_root_texpath = _normalize_graphicspath(images_root_texpath)
        lines += [
            r"\documentclass[11pt]{article}",
            r"\usepackage[margin=2.5cm]{geometry}",
            r"\usepackage{graphicx}",
            r"\usepackage[T1]{fontenc}",
            r"\usepackage[utf8]{inputenc}",
            r"\usepackage{microtype}",
            r"\usepackage[ngerman]{babel}",
            rf"\graphicspath{{{{{images_root_texpath}}}}}",
            r"\setlength{\parindent}{0pt}",
            r"\raggedbottom",
            rf"\title{{{_tex_esc(title)}}}",
            r"\date{}",
            r"\begin{document}",
            r"\maketitle",
            ""
        ]
    lines += [r"% Auto-generated — DO NOT EDIT.", ""]
    if include_macros:
        lines += [
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
        ]
    return lines

def _row_two(cells):
    left  = cells[0] if len(cells) > 0 else ("","")
    right = cells[1] if len(cells) > 1 else ("","")
    def esc_pair(pc):
        p, c = pc
        return (_tex_esc(p), _tex_esc(c))
    (p1, c1) = esc_pair(left); (p2, c2) = esc_pair(right)
    return fr"\ArtRow{{{p1}}}{{{c1}}}{{{p2}}}{{{c2}}}"

def to_tex_variant(rel_path: str) -> str:
    """Aus 'Art/...' → 'Art_TeX/...'. Lässt sonst alles unverändert."""
    if not rel_path:
        return rel_path
    return re.sub(r"^Art/", "Art_TeX/", rel_path)


def regenerate_artist_gallery(artist: str, gallery_file: Path, rows_for_artist,
                               per_page: int, sort_mode: str,
                               standalone: bool, images_root_texpath: str):
    lines = []
    title = f"Art Gallery — {artist}"
    lines += _gallery_preamble(header=standalone, title=title,
                               images_root_texpath=images_root_texpath,
                               include_macros=standalone)
    if standalone:
        lines.append(fr"\section*{{{_tex_esc(artist)}}}")
        lines.append("")

    group = sort_rows(list(rows_for_artist), sort_mode)
    buf = []
    for r in group:
        cap = f"{r.get('artist','')}, {r.get('title','')}" + (f" ({r.get('year','')})" if r.get('year') else "")
        # HIER: auf Art_TeX umbiegen
        fn_rel = r.get("filename","")
        fn_rel_tex = to_tex_variant(fn_rel)
        buf.append((fn_rel_tex, cap))
        if len(buf) == 2:
            if standalone:
                lines.append(_row_two(buf))
            else:
                (p1, c1), (p2, c2) = buf
                lines.append(fr"\noindent\ArtTile{{{_tex_esc(p1)}}}{{{_tex_esc(c1)}}}\hfill"
                             fr"\ArtTile{{{_tex_esc(p2)}}}{{{_tex_esc(c2)}}}\par\vspace{{1.0em}}")
            lines.append("")
            buf = []
    if buf:
        p1, c1 = _tex_esc(buf[0][0]), _tex_esc(buf[0][1])
        lines.append(fr"\noindent\ArtTile{{{p1}}}{{{c1}}}\par\vspace{{1.0em}}")
        lines.append("")

    if standalone:
        lines.append(r"\end{document}")

    gallery_file.write_text("\n".join(lines), encoding="utf-8")


def regenerate_master_gallery(master_path: Path, artists: list[str], galleries_dir: Path,
                              standalone: bool, images_root_texpath: str):
    # Master definiert die Makros zentral.
    title = "Art Gallery — Master"
    lines = _gallery_preamble(header=standalone, title=title,
                              images_root_texpath=images_root_texpath,
                              include_macros=True)
    lines.append(rf"\section*{{{_tex_esc('Artists')}}}")
    lines.append("")
    for a in sorted(artists, key=lambda s: s.lower()):
        s = slug(a)
        lines.append(fr"\subsection*{{{_tex_esc(a)}}}")
        lines.append(fr"\input{{{(galleries_dir / (s + '.tex')).as_posix()}}}")
        lines.append("")
    if standalone:
        lines.append(r"\end{document}")
    master_path.write_text("\n".join(lines), encoding="utf-8")

def rebuild_all_galleries(images_root: Path, per_page: int, sort_mode: str,
                          standalone_master: bool, images_root_texpath: str,
                          artist_standalone: bool, build_master: bool):
    art_dir = images_root / "Art"
    galleries_dir = art_dir / GALLERIES_DIR
    galleries_dir.mkdir(parents=True, exist_ok=True)
    master_path = art_dir / MASTER_GALLERY
    csv_path = art_dir / CSV_NAME

    rows = read_rows(csv_path)
    by_artist = {}
    for r in rows:
        by_artist.setdefault(r.get("artist") or "Unknown Artist", []).append(r)

    for artist, rs in by_artist.items():
        afile = galleries_dir / f"{slug(artist)}.tex"
        regenerate_artist_gallery(
            artist, afile, rs, per_page=per_page, sort_mode=sort_mode,
            standalone=artist_standalone, images_root_texpath=images_root_texpath
        )

    if build_master and not artist_standalone:
        regenerate_master_gallery(master_path, list(by_artist.keys()), galleries_dir,
                                  standalone=standalone_master, images_root_texpath=images_root_texpath)
        return master_path, galleries_dir
    else:
        return None, galleries_dir

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
def _ensure_dirs(images_root: Path):
    art_dir = images_root / "Art"
    art_dir.mkdir(parents=True, exist_ok=True)
    (art_dir / GALLERIES_DIR).mkdir(parents=True, exist_ok=True)
    return art_dir

def _update_artist_and_master(images_root: Path, artist_name: str, per_page: int, sort_mode: str,
                              standalone_master: bool, images_root_texpath: str,
                              artist_standalone: bool, build_master: bool):
    art_dir = images_root / "Art"
    galleries_dir = art_dir / GALLERIES_DIR
    master_path = art_dir / MASTER_GALLERY
    csv_path = art_dir / CSV_NAME

    rows = read_rows(csv_path)
    artist_key = artist_name or "Unknown Artist"
    artist_rows = [r for r in rows if (r.get("artist") or "Unknown Artist") == artist_key]

    regenerate_artist_gallery(
        artist_key, galleries_dir / f"{slug(artist_key)}.tex", artist_rows,
        per_page=per_page, sort_mode=sort_mode,
        standalone=artist_standalone, images_root_texpath=images_root_texpath
    )

    if build_master and not artist_standalone:
        artists = sorted({(r.get("artist") or "Unknown Artist") for r in rows})
        regenerate_master_gallery(master_path, artists, galleries_dir,
                                  standalone=standalone_master, images_root_texpath=images_root_texpath)

def fetch_artist(name: str, limit: int, images_root: Path,
                 per_page: int, sort_mode: str,
                 standalone_master: bool, images_root_texpath: str,
                 min_width: int, min_height: int,
                 artist_standalone: bool, build_master: bool):
    art_dir = _ensure_dirs(images_root)
    csv_path = art_dir / CSV_NAME
    hash_idx = load_hash_index(art_dir)

    ensure_index(csv_path)
    rows = read_rows(csv_path)
    seen = load_seen(csv_path)

    qid, label = resolve_artist_qid(name)
    print(f"[wikidata] {name} → {qid} ({label})")
    items = wikidata_fetch_items(qid, limit * 2)
    print(f"[wikidata] candidate items with images:", len(items))

    saved = 0
    for title, img_iri, year in items:
        if saved >= limit:
            break

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
        fn = f"{uid}__{slug(name)[:60]}__{slug(title)[:90]}{('__' + slug(year)) if year else ''}{ext}"
        path = (images_root / "Art" / fn)

        # 1) Original herunterladen (+ ggf. TIFF → JPG)
        try:
            with retry_get(direct, headers=UA, timeout=90, retries=3, stream=True) as rr:
                with open(path, "wb") as f:
                    for chunk in rr.iter_content(8192):
                        if chunk:
                            f.write(chunk)
            if mime in ("image/tif", "image/tiff"):
                print("[convert] TIFF → JPG:", path.name)
                path = convert_tiff_to_jpg(path)
        except Exception as e:
            print(f"[warn] download/convert failed: {e}")
            try:
                path.unlink()
            except Exception:
                pass
            continue  # ohne Datei geht's nicht weiter

        # 2) pHash berechnen und Duplikate filtern
        try:
            ph = compute_phash(path)
        except Exception as e:
            print(f"[warn] phash failed: {e}")
            try:
                path.unlink()
            except Exception:
                pass
            continue

        if is_similar_hash(ph, list(hash_idx.values())):
            print("[skip] duplicate (phash):", path.name)
            try:
                path.unlink()
            except Exception:
                pass
            continue

        # 3) TeX-Kopie (verkleinert) anlegen – Fehler hier sind nicht kritisch
        try:
            tex_dir = images_root / "Art_TeX"
            tex_dir.mkdir(parents=True, exist_ok=True)
            tex_path = tex_dir / path.name
            with Image.open(path) as im:
                im.thumbnail((1600, 1600), Image.LANCZOS)  # Max-Kante 1600px
                im.save(tex_path, quality=85, optimize=True)
        except Exception as e:
            print(f"[warn] TeX-Kopie nicht erstellt: {e}")

        # 4) CSV + Hash-Index aktualisieren
        rel = path.relative_to(images_root).as_posix()
        rows.append({
            "uid": uid,
            "filename": rel,  # Hinweis: Für LaTeX kannst du beim Rendern auf Art_TeX umschalten.
            "artist": name,
            "title": title,
            "year": year,
            "source": "WIKIDATA+COMMONS",
            "license": lic,
            "movement": "",
            "keywords": ""
        })
        write_rows(csv_path, rows)
        hash_idx[uid] = ph.__str__()
        save_hash_index(art_dir, hash_idx)

        seen.add(sig)
        saved += 1
        print(f"[saved] {uid} — {name} — {title} ({year})")

        _update_artist_and_master(
            images_root, name, per_page, sort_mode,
            standalone_master, images_root_texpath,
            artist_standalone, build_master
        )
        time.sleep(0.1)

    _update_artist_and_master(
        images_root, name, per_page, sort_mode,
        standalone_master, images_root_texpath,
        artist_standalone, build_master
    )
    print(
        f"\nDone. Saved {saved} files."
        f"\nCSV: {csv_path}\nMaster: {art_dir / MASTER_GALLERY}\nGalleries: {art_dir / GALLERIES_DIR}"
    )


def fetch_work(work_title: str, work_artist_name: str | None, limit: int, images_root: Path,
               per_page: int, sort_mode: str, standalone_master: bool, images_root_texpath: str,
               min_width: int, min_height: int, artist_standalone: bool, build_master: bool):
    art_dir = _ensure_dirs(images_root)
    csv_path = art_dir / CSV_NAME
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
        if not direct or not any(k in lic for k in ALLOWED_LIC): continue
        if width < min_width or height < min_height: continue

        artist_for_sig = work_artist_name or artist_label or "Unknown Artist"
        sig = make_sig(artist_for_sig, title, year)
        if sig in seen:
            print("[skip] already seen:", sig); continue

        uid = next_uid(rows)
        ext = Path(urllib.parse.urlparse(direct).path).suffix or ".jpg"
        artist_slug = slug(artist_for_sig)[:60]
        fn = f"{uid}__{artist_slug}__{slug(title)[:90]}{('__'+slug(year)) if year else ''}{ext}"
        path = (images_root / "Art" / fn)

        # Original speichern
        try:
            with retry_get(direct, headers=UA, timeout=90, retries=3, stream=True) as rr:
                with open(path, "wb") as f:
                    for chunk in rr.iter_content(8192):
                        if chunk:
                            f.write(chunk)
            if mime in ("image/tif", "image/tiff"):
                print("[convert] TIFF → JPG:", path.name)
                path = convert_tiff_to_jpg(path)
        except Exception as e:
            print(f"[warn] Fehler beim Speichern des Originals: {e}")

        # --- NEU: verkleinerte TeX-Version speichern ---
        try:
            tex_dir = images_root / "Art_TeX"
            tex_dir.mkdir(parents=True, exist_ok=True)

            tex_path = tex_dir / path.name
            with Image.open(path) as im:
                im.thumbnail((1600, 1600), Image.LANCZOS)  # Max 1600px in Breite/Höhe
                im.save(tex_path, quality=85, optimize=True)
        except Exception as e:
            print(f"[warn] TeX-Kopie nicht erstellt: {e}")

        # -----------------------------------------------


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
            "artist": artist_for_sig, "title": title, "year": year,
            "source": "WIKIDATA+COMMONS", "license": lic,
            "movement": "", "keywords": ""
        })
        write_rows(csv_path, rows)
        hash_idx[uid] = ph.__str__(); save_hash_index(art_dir, hash_idx)

        saved += 1
        print(f"[saved] {uid} — {artist_for_sig} — {title} ({year})")
        _update_artist_and_master(images_root, artist_for_sig, per_page, sort_mode,
                                  standalone_master, images_root_texpath,
                                  artist_standalone, build_master)
        time.sleep(0.1)

    if work_artist_name or artist_label:
        _update_artist_and_master(images_root, work_artist_name or artist_label, per_page, sort_mode,
                                  standalone_master, images_root_texpath,
                                  artist_standalone, build_master)

    print(f"\nDone (work mode). Saved {saved} files."
          f"\nCSV: {csv_path}\nMaster: {art_dir / MASTER_GALLERY}\nGalleries: {art_dir / GALLERIES_DIR}")

def fetch_commons_file(file_title_no_prefix: str, artist_hint: str | None, images_root: Path,
                       per_page: int, sort_mode: str, standalone_master: bool, images_root_texpath: str,
                       min_width: int, min_height: int, artist_standalone: bool, build_master: bool):

    art_dir = _ensure_dirs(images_root)
    csv_path = art_dir / CSV_NAME
    hash_idx = load_hash_index(art_dir)

    ensure_index(csv_path)
    rows = read_rows(csv_path)
    seen = load_seen(csv_path)

    lic, direct, mime, width, height = commons_license_and_direct_url(file_title_no_prefix)
    if not direct: raise SystemExit(f"Commons-Datei nicht gefunden: {file_title_no_prefix}")
    if not any(k in lic for k in ALLOWED_LIC): raise SystemExit(f"Nicht erlaubte Lizenz: {lic}")
    if width < min_width or height < min_height: raise SystemExit(f"Zu geringe Auflösung: {width}x{height}")

    base = Path(file_title_no_prefix).stem.replace("_", " ").strip()
    title_guess, year_guess = base, ""
    artist_name = artist_hint or "Unknown Artist"

    sig = make_sig(artist_name, title_guess, year_guess)
    if sig in seen:
        print("[skip] already in index:", sig)
        return

    # ---- 1) Download ins temp-Ziel (noch ohne UID) ----
    tmp_path = images_root / "Art" / f"__tmp__{slug(base)[:90]}"
    ext = Path(urllib.parse.urlparse(direct).path).suffix or ".jpg"
    tmp_path = tmp_path.with_suffix(ext)
    try:
        with retry_get(direct, headers=UA, timeout=90, retries=3, stream=True) as rr:
            with open(tmp_path, "wb") as f:
                for chunk in rr.iter_content(8192):
                    if chunk: f.write(chunk)
        if mime in ("image/tif", "image/tiff"):
            print("[convert] TIFF → JPG:", tmp_path.name)
            tmp_path = convert_tiff_to_jpg(tmp_path)
    except Exception as e:
        print(f"[warn] download/convert failed: {e}")
        try: tmp_path.unlink()
        except: pass
        return

    # ---- 2) pHash VOR UID / VOR TeX prüfen ----
    try:
        ph = compute_phash(tmp_path)

        # --- neu: Distanz + nächste UID bestimmen ---
        dist, uid_match = nearest_phash_match(ph, hash_idx)
        print(f"[debug] phash={ph} nearest={uid_match} dist={dist}")

        # --- Duplikat-Entscheidung ---
        if dist <= PHASH_DISTANCE_MAX:
            print(f"[skip] duplicate (phash ≤ {PHASH_DISTANCE_MAX}):",
                tmp_path.name, "closest=", uid_match, "dist=", dist)
            try:
                tmp_path.unlink()
            except:
                pass
            return
    except Exception as e:
        print("[warn] phash failed:", e)
        try:
            tmp_path.unlink()
        except:
            pass
        return


    # ---- 3) Jetzt UID vergeben & in finalen Namen umbenennen ----
    uid = next_uid(rows)
    artist_slug = slug(artist_name)[:60]
    final_name = f"{uid}__{artist_slug}__{slug(title_guess)[:90]}{tmp_path.suffix}"
    path = (images_root / "Art" / final_name)
    tmp_path.rename(path)

    # ---- 4) TeX-Kopie erzeugen ----
    try:
        tex_dir = images_root / "Art_TeX"; tex_dir.mkdir(parents=True, exist_ok=True)
        tex_path = tex_dir / path.name
        with Image.open(path) as im:
            im.thumbnail((1600, 1600), Image.LANCZOS)
            im.save(tex_path, quality=85, optimize=True)
    except Exception as e:
        print(f"[warn] TeX-Kopie nicht erstellt: {e}")

    # ---- 5) CSV + Hash-Index ----
    rel = path.relative_to(images_root).as_posix()
    rows.append({
        "uid": uid, "filename": rel, "artist": artist_name, "title": title_guess, "year": year_guess,
        "source": "COMMONS", "license": lic, "movement": "", "keywords": ""
    })
    write_rows(csv_path, rows)
    hash_idx[uid] = ph.__str__(); save_hash_index(art_dir, hash_idx)

    _update_artist_and_master(images_root, artist_name, per_page, sort_mode,
                              standalone_master, images_root_texpath, artist_standalone, build_master)
    print("Done (commons file).")


def fetch_commons_category(category: str, limit: int, images_root: Path,
                           per_page: int, sort_mode: str, standalone_master: bool, images_root_texpath: str,
                           min_width: int, min_height: int, artist_standalone: bool, build_master: bool):

    art_dir = _ensure_dirs(images_root)
    csv_path = art_dir / CSV_NAME
    hash_idx = load_hash_index(art_dir)

    ensure_index(csv_path)
    rows = read_rows(csv_path)
    seen = load_seen(csv_path)

    saved, cmcontinue = 0, None
    while saved < limit:
        params = {"action":"query","format":"json","list":"categorymembers",
                  "cmtitle":f"Category:{category}","cmtype":"file","cmlimit":50}
        if cmcontinue: params["cmcontinue"] = cmcontinue

        r = retry_get("https://commons.wikimedia.org/w/api.php", params, UA, timeout=40).json()
        members = (r.get("query", {}).get("categorymembers") or [])
        if not members: break

        for m in members:
            if saved >= limit: break
            title = m.get("title",""); 
            if not title.startswith("File:"): continue
            file_title_no_prefix = title.split("File:",1)[1]

            lic, direct, mime, width, height = commons_license_and_direct_url(file_title_no_prefix)
            if not direct or not any(k in lic for k in ALLOWED_LIC): continue
            if width < min_width or height < min_height: continue

            artist_name = artist_from_category(category)
            base = Path(file_title_no_prefix).stem.replace("_"," ").strip()
            title_guess, year_guess = base, ""

            sig = make_sig(artist_name, title_guess, year_guess)
            if sig in seen: continue

            # --- Download temp ---
            tmp_path = images_root / "Art" / f"__tmp__{slug(base)[:90]}"
            ext = Path(urllib.parse.urlparse(direct).path).suffix or ".jpg"
            tmp_path = tmp_path.with_suffix(ext)
            try:
                with retry_get(direct, headers=UA, timeout=90, retries=3, stream=True) as rr:
                    with open(tmp_path,"wb") as f:
                        for chunk in rr.iter_content(8192):
                            if chunk: f.write(chunk)
                if mime in ("image/tif","image/tiff"):
                    print("[convert] TIFF → JPG:", tmp_path.name)
                    tmp_path = convert_tiff_to_jpg(tmp_path)
            except Exception as e:
                print("[warn] download/convert failed:", e)
                try: tmp_path.unlink()
                except: pass
                continue

            # --- pHash vor UID/TeX ---
            try:
                ph = compute_phash(tmp_path)
                dist, uid_match = nearest_phash_match(ph, hash_idx)
                print(f"[debug] phash={ph} nearest={uid_match} dist={dist}")

                if dist <= PHASH_DISTANCE_MAX:
                    print(f"[skip] duplicate (phash ≤ {PHASH_DISTANCE_MAX}):",
                        tmp_path.name, "closest=", uid_match, "dist=", dist)
                    try:
                        tmp_path.unlink()
                    except:
                        pass
                    continue

            except Exception as e:
                print("[warn] phash failed:", e)
                try: tmp_path.unlink()
                except: pass
                continue

            # --- UID + final rename ---
            uid = next_uid(rows)
            final_name = f"{uid}__{slug(artist_name)[:60]}__{slug(title_guess)[:90]}{tmp_path.suffix}"
            path = (images_root / "Art" / final_name)
            tmp_path.rename(path)

            # --- TeX-Kopie ---
            try:
                tex_dir = images_root / "Art_TeX"; tex_dir.mkdir(parents=True, exist_ok=True)
                tex_path = tex_dir / path.name
                with Image.open(path) as im:
                    im.thumbnail((1600,1600), Image.LANCZOS)
                    im.save(tex_path, quality=85, optimize=True)
            except Exception as e:
                print(f"[warn] TeX-Kopie nicht erstellt: {e}")

            # --- CSV + Index ---
            rel = path.relative_to(images_root).as_posix()
            rows.append({
                "uid": uid, "filename": rel, "artist": artist_name, "title": title_guess, "year": year_guess,
                "source": "COMMONS_CATEGORY", "license": lic, "movement": "", "keywords": ""
            })
            write_rows(csv_path, rows)
            hash_idx[uid] = ph.__str__(); save_hash_index(art_dir, hash_idx)

            seen.add(sig); saved += 1
            print(f"[saved] {uid} — {artist_name} — {title_guess}")
            _update_artist_and_master(images_root, artist_name, per_page, sort_mode,
                                      standalone_master, images_root_texpath, artist_standalone, build_master)

        cmcontinue = (r.get("continue") or {}).get("cmcontinue")
        if not cmcontinue: break

    _update_artist_and_master(images_root, artist_from_category(category), per_page, sort_mode,
                              standalone_master, images_root_texpath, artist_standalone, build_master)
    print(f"\nDone (commons category). Saved {saved} files.")


# ---------- CLI ----------
def main():
    ap = argparse.ArgumentParser(description="Fetch artist/work images via Wikidata (P18) + Commons; per-artist gallery builder.")
    ap.add_argument("--artist", help='z.B. "Wassily Kandinsky"')
    ap.add_argument("--work", type=str, help='Werk-/Titel-Suche, z.B. "Intersecting Lines"')
    ap.add_argument("--work-artist", type=str, help='(Optional) Künstlername zur Eingrenzung')

    ap.add_argument("--commons-file", type=str, help='Direkter Commons-Dateiname')
    ap.add_argument("--commons-category", type=str, help='Commons-Kategorie ohne "Category:"')

    ap.add_argument("--limit", type=int, default=300)
    ap.add_argument("--images-root", type=str, default=None)

    # Gallerie-/Master-Layout:
    ap.add_argument("--artist-standalone", dest="artist_standalone", action="store_true",
                    help="Künstler-Galerien MIT Header (Standalone). (Default)")
    ap.add_argument("--no-artist-standalone", dest="artist_standalone", action="store_false",
                    help="Künstler-Galerien als Fragmente OHNE Header erzeugen.")
    ap.set_defaults(artist_standalone=True)

    ap.add_argument("--build-master", action="store_true",
                    help="Master bauen, der alle Künstler-Fragmente via \\input{} einbindet. "
                         "Nur sinnvoll mit --no-artist-standalone.")
    ap.add_argument("--rebuild-only", action="store_true",
                    help="Galerien (und optional Master) aus CSV neu erzeugen")

    ap.add_argument("--per-page", type=int, default=6, help="Bilder pro Seite (3x2)")
    ap.add_argument("--sort", type=str, default="uid", choices=["uid","artist","year","title"], help="Sortierung")
    ap.add_argument("--standalone", action="store_true", help="Master mit Header erzeugen (falls gebaut)")
    ap.add_argument("--image-root-texpath", type=str,
                    default="/Users/tim/NoteDeck/MainDeck-modular/Library/Images/",
                    help="Pfad für \\graphicspath im Header")
    ap.add_argument("--min-width", type=int, default=2000)
    ap.add_argument("--min-height", type=int, default=2000)
    args = ap.parse_args()

    # normalisiere graphicspath (Slash am Ende)
    args.image_root_texpath = _normalize_graphicspath(args.image_root_texpath)

    images_root = resolve_images_root(args.images_root)
    _ensure_dirs(images_root)
    csv_path = images_root / "Art" / CSV_NAME

    if args.rebuild_only:
        master_path, galleries_dir = rebuild_all_galleries(
            images_root, per_page=args.per_page, sort_mode=args.sort,
            standalone_master=args.standalone, images_root_texpath=args.image_root_texpath,
            artist_standalone=args.artist_standalone, build_master=args.build_master
        )
        print("Rebuilt.")
        print(f"CSV: {csv_path}")
        if master_path: print(f"Master: {master_path}")
        print(f"Galleries: {galleries_dir}")
        return

    common_kwargs = dict(
        per_page=args.per_page, sort_mode=args.sort,
        standalone_master=args.standalone, images_root_texpath=args.image_root_texpath,
        min_width=args.min_width, min_height=args.min_height,
        artist_standalone=args.artist_standalone, build_master=args.build_master
    )

    if args.commons_category:
        fetch_commons_category(args.commons_category, args.limit, images_root, **common_kwargs)
        return

    if args.commons_file:
        fetch_commons_file(args.commons_file, args.work_artist, images_root, **common_kwargs)
        return

    if args.work is not None or args.work_artist:
        fetch_work(args.work or "", args.work_artist, args.limit, images_root, **common_kwargs)
        return

    if not args.artist:
        raise SystemExit("Fehler: --artist erforderlich (oder --work/--commons-file/--commons-category/--rebuild-only).")

    if not (args.artist or args.work or args.commons_file or args.commons_category 
            or args.rebuild_only or args.work_artist):
        print("Fehler: --artist erforderlich (oder --work/--commons-file/--commons-category/--rebuild-only).")
        sys.exit(1)

    fetch_artist(args.artist, args.limit, images_root, **common_kwargs)

if __name__ == "__main__":
    main()
