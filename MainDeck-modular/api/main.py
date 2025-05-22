from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from pathlib import Path
import json
import subprocess
import os

app = FastAPI(title="NoteDeck-API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Globale Pfade ===
BASE_DIR         = Path(__file__).resolve().parents[1]
LIB_JSON         = BASE_DIR / "Library" / "Library.json"
TOPICMAP_JSON    = BASE_DIR / "Library" / "SubjectsTopics.json"
LIB_TEX          = BASE_DIR / "Library" / "Library.tex"
SOURCE_DIR       = BASE_DIR / "Sources"
EXPORT_DIR       = BASE_DIR / "Export"
EXPORT_SCRIPT    = Path("export_builder.py").resolve()

# === Modelle ===
class SnipRequest(BaseModel):
    Subject: str
    Topic: str
    LitID: str
    CTyp: str
    Content: str
    Body: str
    ParentTopic: str
    project: str  # ⬅️ NEU

class TopicAddRequest(BaseModel):
    Subject: str
    Topic: str
    ParentTopic: str | None = None

class SaveSourceRequest(BaseModel):
    project: str
    content: str

# === Snip-Endpunkt ===
@app.post("/snip")
def create_snip(req: SnipRequest):
    import re

    if not LIB_JSON.exists():
        raise HTTPException(status_code=500, detail="Library.json not found")
    if not TOPICMAP_JSON.exists():
        raise HTTPException(status_code=500, detail="SubjectsTopics.json not found")

    # Lade beide JSON-Dateien
    with LIB_JSON.open("r", encoding="utf-8") as f:
        data = json.load(f)
    with TOPICMAP_JSON.open("r", encoding="utf-8") as f:
        topicmap = json.load(f)

    # Ermittle TopicIndex aus der Strukturdatei
    try:
        topic_index = topicmap[req.Subject]["topics"][req.Topic]["index"]
    except KeyError:
        raise HTTPException(status_code=400, detail=f"Topic index for '{req.Subject} – {req.Topic}' not found")

    # Ermittle nächste freie Nummer für dieses Topic
    matching = [
        d for d in data
        if d["Subject"] == req.Subject and d["LitID"] == req.LitID and d["Topic"] == req.Topic
    ]
    next_number = max([int(d["UnitID"].split("-")[-1]) for d in matching], default=0) + 1

    unit_id = f"{req.Subject}-{req.LitID}-{topic_index:02d}-{next_number:02d}"

    # === JSON-Eintrag
    new_entry = {
        "UnitID": unit_id,
        "Subject": req.Subject,
        "Topic": req.Topic,
        "CTyp": req.CTyp,
        "Content": req.Content,
        "LitID": req.LitID,
        "Layer": None,
        "Comp": None,
        "RelInt": None,
        "RelId": None,
        "Cont": None,
        "Cint": 0.0,
        "CID": 0.0,
        "ParentTopic": req.ParentTopic,
        "TopicPath": f"{req.ParentTopic}/{req.Topic}"
        # "Body": req.Body
    }

    data.append(new_entry)
    with LIB_JSON.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    # === Modul erzeugen
#     MODULE_DIR = BASE_DIR / "Library" / "Module"
#     MODULE_DIR.mkdir(parents=True, exist_ok=True)
#     module_path = MODULE_DIR / f"{unit_id}.tex"
#     module_content = f"""% Auto‑generiert aus Library.tex
# % UnitID: {unit_id}
# % Titel : {req.Content}

# \\begin{{{req.CTyp}}}{{{unit_id}}}{{{req.Content}}}
# {req.Body}
# \\end{{{req.CTyp}}}
# """
#     module_path.write_text(module_content, encoding="utf-8")

    # === Source-Datei ersetzen
    safe_project = req.project.replace("/", "").replace("..", "")
    source_path = SOURCE_DIR / safe_project / f"{safe_project}.tex"
    if not source_path.exists():
        raise HTTPException(status_code=404, detail="Quelldatei nicht gefunden")

    source_code = source_path.read_text(encoding="utf-8")
    escaped_body = re.escape(req.Body.strip())
    pattern = re.compile(escaped_body, re.DOTALL)

    match = pattern.search(source_code)
    if not match:
        raise HTTPException(status_code=400, detail="Markierter Body nicht exakt in Source-Datei gefunden.")

    start, end = match.span()
    replacement = f"\\begin{{{req.CTyp}}}{{{unit_id}}}{{{req.Content}}}\n{req.Body}\n\\end{{{req.CTyp}}}"
    new_code = source_code[:start] + replacement + source_code[end:]

    source_path.write_text(new_code, encoding="utf-8")

    return {"status": "success", "UnitID": unit_id}



# === TopicMap-Endpunkte ===
@app.get("/topic-map")
def get_topic_map():
    if not TOPICMAP_JSON.exists():
        raise HTTPException(status_code=404, detail="SubjectsTopics.json not found")
    return json.loads(TOPICMAP_JSON.read_text(encoding="utf-8"))

@app.post("/add-topic")
def add_topic(req: TopicAddRequest):
    if not TOPICMAP_JSON.exists():
        raise HTTPException(status_code=404, detail="SubjectsTopics.json not found")

    with TOPICMAP_JSON.open("r", encoding="utf-8") as f:
        data = json.load(f)

    subj = req.Subject
    topic = req.Topic
    parent = req.ParentTopic

    if subj not in data:
        data[subj] = {
            "index": max([v["index"] for v in data.values()], default=0) + 1,
            "topics": {}
        }

    if topic in data[subj]["topics"]:
        return {
            "status": "exists",
            "TopicPath": f"{parent}/{topic}" if parent else topic
        }

    next_index = max([t["index"] for t in data[subj]["topics"].values()], default=0) + 1
    data[subj]["topics"][topic] = {
        "index": next_index,
        "parent": parent
    }

    with TOPICMAP_JSON.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    topic_path = f"{parent}/{topic}" if parent else topic
    return {
        "status": "added",
        "Topic": topic,
        "Subject": subj,
        "TopicPath": topic_path,
        "index": next_index
    }

# === Source-Dateien ===
@app.get("/available-sources")
def available_sources():
    sources = []
    for subfolder in SOURCE_DIR.iterdir():
        if subfolder.is_dir():
            tex_file = subfolder / (subfolder.name + ".tex")
            if tex_file.exists():
                rel_path = tex_file.relative_to(SOURCE_DIR)
                sources.append(str(rel_path))
    return sources

@app.get("/load-source")
def load_source(project: str):
    safe = project.replace("/", "").replace("..", "")
    tex_path = SOURCE_DIR / safe / f"{safe}.tex"
    if not tex_path.exists():
        raise HTTPException(status_code=404, detail=f"{tex_path} not found")
    content = tex_path.read_text(encoding="utf-8")
    return {"filename": f"{safe}.tex", "content": content}

@app.post("/save-source")
def save_source(req: SaveSourceRequest):
    safe = req.project.replace("/", "").replace("..", "")
    tex_path = SOURCE_DIR / safe / f"{safe}.tex"
    if not tex_path.exists():
        raise HTTPException(status_code=404, detail=f"{tex_path} not found")
    tex_path.write_text(req.content, encoding="utf-8")
    return {"status": "saved", "project": safe}

# === Bestehende Funktionen ===
def load_units():
    if not LIB_JSON.exists():
        return []
    return json.loads(LIB_JSON.read_text(encoding="utf-8"))

@app.get("/units")
def get_units(subject: str | None = None,
              topic: str | None = None,
              layer: int  | None = None,
              comp:  int  | None = None):
    data = load_units()
    def match(u):
        return ((subject is None or u["Subject"] == subject) and
                (topic   is None or u["Topic"]   == topic)   and
                (layer   is None or str(u.get("Layer")) == str(layer)) and
                (comp    is None or str(u.get("Comp"))  == str(comp)))
    return [u for u in data if match(u)]

@app.post("/export-project/{project_name}")
async def backup_project_only_json(project_name: str, request: Request):
    try:
        body = await request.json()
        EXPORT_DIR.mkdir(parents=True, exist_ok=True)
        json_path = EXPORT_DIR / f"{project_name}.json"
        json_path.write_text(json.dumps(body, indent=2, ensure_ascii=False), encoding="utf-8")
        return {"status": "ok", "path": str(json_path.relative_to(BASE_DIR))}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/export-tex/{project_name}")
def export_tex_file(project_name: str):
    try:
        subprocess.run(
            ["python3", str(EXPORT_SCRIPT), project_name],
            cwd=os.path.dirname(__file__),
            check=True,
            capture_output=True,
            text=True
        )
        return {"status": "success", "message": f"{project_name} wurde als .tex exportiert."}
    except subprocess.CalledProcessError as e:
        return {"status": "error", "message": e.stderr.strip() or str(e)}
    except Exception as e:
        return {"status": "error", "message": str(e)}
