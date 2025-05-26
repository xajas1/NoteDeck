from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Request, HTTPException, Body, HTTPException
from pydantic import BaseModel
from pathlib import Path
import json
import subprocess
import os
import re
import uuid

app = FastAPI(title="NoteDeck-API")
print("🚀 FastAPI loaded")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
print("🔧 CORS Middleware konfiguriert")

class ReplaceBodyRequest(BaseModel):
    UID: str
    project: str
    newBody: str
    Content: str
    CTyp: str

# === Globale Pfade ===
BASE_DIR         = Path(__file__).resolve().parents[1]
LIB_JSON         = BASE_DIR / "Library" / "Library.json"
TOPICMAP_JSON    = BASE_DIR / "Library" / "SubjectsTopics.json"
SOURCEMAP_JSON   = BASE_DIR / "Library" / "SourceMap.json"
PROJECTS_JSON    = BASE_DIR / "Library" / "snipProjects.json"
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
    project: str

class TopicAddRequest(BaseModel):
    Subject: str
    Topic: str
    ParentTopic: str | None = None

class SaveSourceRequest(BaseModel):
    project: str
    content: str

class UpdateUnitRequest(BaseModel):
    UnitID: str
    field: str
    value: str | float | int | None

class SaveSnipProjectRequest(BaseModel):
    project_name: str
    data: dict

class LoadSnipProjectRequest(BaseModel):
    project_name: str

# === Projekte ===
@app.get("/snip-projects")
def list_snip_projects():
    if not PROJECTS_JSON.exists():
        return {}
    return json.loads(PROJECTS_JSON.read_text(encoding="utf-8"))

@app.post("/save-snip-project")
def save_snip_project(req: SaveSnipProjectRequest):
    projects = {}
    if PROJECTS_JSON.exists():
        projects = json.loads(PROJECTS_JSON.read_text(encoding="utf-8"))
    projects[req.project_name] = req.data
    PROJECTS_JSON.write_text(json.dumps(projects, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"status": "saved", "project_name": req.project_name}

@app.post("/load-snip-project")
def load_snip_project(req: LoadSnipProjectRequest):
    if not PROJECTS_JSON.exists():
        raise HTTPException(status_code=404, detail="snipProjects.json not found")
    projects = json.loads(PROJECTS_JSON.read_text(encoding="utf-8"))
    if req.project_name not in projects:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")
    return projects[req.project_name]

@app.post("/replace-body")
def replace_body(req: ReplaceBodyRequest):
    import re

    if not LIB_JSON.exists():
        raise HTTPException(status_code=500, detail="Library.json not found")

    # Library laden
    data = json.loads(LIB_JSON.read_text(encoding="utf-8"))
    unit = next((u for u in data if u["UID"] == req.UID), None)

    if not unit:
        raise HTTPException(status_code=404, detail=f"Unit mit UID {req.UID} nicht gefunden")

    # Quelldatei laden
    source_path = SOURCE_DIR / req.project
    if not source_path.exists():
        raise HTTPException(status_code=404, detail=f"Quelldatei nicht gefunden: {source_path}")

    tex = source_path.read_text(encoding="utf-8")

    # Alte Umgebung entfernen, wenn vorhanden
    if unit.get("Body"):
        envname = unit["CTyp"]
        pattern = rf"\\begin{{{envname}}}{{{re.escape(unit['UnitID'])}}}{{.*?}}\n(.*?)\n\\end{{{envname}}}"
        tex, count = re.subn(pattern, "", tex, flags=re.DOTALL)
        print(f"🧹 Alte Umgebung entfernt: {count} Vorkommen")

    # Neue Umgebung einfügen (z. B. an Cursorstelle später)
    replacement = f"\\begin{{{req.CTyp}}}{{{unit['UnitID']}}}{{{req.Content}}}\n{req.newBody}\n\\end{{{req.CTyp}}}"

    # Für jetzt: einfach am Ende anhängen
    tex += "\n\n" + replacement.strip() + "\n"

    # Schreiben
    source_path.write_text(tex.strip(), encoding="utf-8")

    # Library aktualisieren
    unit["Body"] = req.newBody
    unit["Content"] = req.Content
    unit["CTyp"] = req.CTyp

    with LIB_JSON.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return {"status": "success", "unit": unit}


@app.get("/list-splitstates")
def list_splitstates():
    if not PROJECTS_JSON.exists() or PROJECTS_JSON.stat().st_size == 0:
        return []
    try:
        data = json.loads(PROJECTS_JSON.read_text(encoding="utf-8"))
        return list(data.keys())
    except json.JSONDecodeError:
        return []

@app.delete("/delete-snip-project")
def delete_snip_project(project: str):
    if not PROJECTS_JSON.exists():
        raise HTTPException(status_code=404, detail="snipProjects.json not found")
    data = json.loads(PROJECTS_JSON.read_text(encoding="utf-8"))
    if project in data:
        del data[project]
        PROJECTS_JSON.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"status": "deleted"}


# === Load Units nach Source (über SourceMap) ===
@app.get("/load-library")
def load_library(source: str = ""):
    if not LIB_JSON.exists():
        raise HTTPException(status_code=500, detail="Library.json not found")

    data = json.loads(LIB_JSON.read_text(encoding="utf-8"))

    if not source:
        return data

    if not SOURCEMAP_JSON.exists():
        raise HTTPException(status_code=500, detail="SourceMap.json not found")

    source_map_raw = SOURCEMAP_JSON.read_text(encoding="utf-8")
    print("📄 Gelesene source_map.json:", source_map_raw)

    source_map = json.loads(source_map_raw)

    print(f"📥 Request für source = {source}")
    print(f"🔍 source_map.get({source}) = {source_map.get(source)}")

    litid = source_map.get(source)
    if not litid:
        print("⚠️ Keine LitID für Source gefunden.")
        return []

    result = [u for u in data if u.get("LitID") == litid]
    print(f"✅ Gefundene Units für LitID {litid}: {len(result)}")
    return result

@app.post("/update-unit")
def update_unit(req: UpdateUnitRequest):
    allowed_fields = {"Layer", "Comp", "RelInt", "RelId", "Cont", "Cint", "CID"}

    if req.field not in allowed_fields:
        raise HTTPException(
            status_code=400,
            detail=f"Field '{req.field}' not allowed in update-unit. Use rename-unit or update-env-or-content."
        )

    if not LIB_JSON.exists():
        raise HTTPException(status_code=500, detail="Library.json not found")

    with LIB_JSON.open("r", encoding="utf-8") as f:
        data = json.load(f)

    found = False
    for entry in data:
        if entry["UnitID"] == req.UnitID:
            entry[req.field] = req.value
            found = True
            break

    if not found:
        raise HTTPException(status_code=404, detail=f"Unit {req.UnitID} not found")

    with LIB_JSON.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return {
        "status": "updated",
        "UnitID": req.UnitID,
        "field": req.field,
        "value": req.value
    }

@app.post("/snip")
def create_snip(req: SnipRequest):
    import re

    if not LIB_JSON.exists():
        raise HTTPException(status_code=500, detail="Library.json not found")
    if not TOPICMAP_JSON.exists():
        raise HTTPException(status_code=500, detail="SubjectsTopics.json not found")

    with LIB_JSON.open("r", encoding="utf-8") as f:
        data = json.load(f)
    with TOPICMAP_JSON.open("r", encoding="utf-8") as f:
        topicmap = json.load(f)

    try:
        topic_index = topicmap[req.Subject]["topics"][req.Topic]["index"]
    except KeyError:
        raise HTTPException(status_code=400, detail=f"Topic index for '{req.Subject} – {req.Topic}' not found")

    matching = [
        d for d in data
        if d["Subject"] == req.Subject and d["LitID"] == req.LitID and d["Topic"] == req.Topic
    ]
    next_number = max([int(d["UnitID"].split("-")[-1]) for d in matching], default=0) + 1
    unit_id = f"{req.Subject}-{req.LitID}-{topic_index:02d}-{next_number:02d}"

    new_entry = {
        "UID": str(uuid.uuid4()),
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
        "TopicPath": f"{req.ParentTopic}/{req.Topic}",
        "Body": req.Body
    }

    data.append(new_entry)

    with LIB_JSON.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    # --- Sichere Pfadbehandlung ---
    if ".." in req.project or req.project.startswith("/"):
        raise HTTPException(status_code=400, detail="Unsicherer Pfad")
    source_path = SOURCE_DIR / req.project

    if not source_path.exists():
        raise HTTPException(status_code=404, detail=f"Quelldatei nicht gefunden: {source_path}")

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

    return {"status": "success", "UnitID": unit_id, "unit": new_entry}

@app.get("/source-map")
def get_source_map():
    if not SOURCEMAP_JSON.exists():
        raise HTTPException(status_code=404, detail="SourceMap.json not found")
    return json.loads(SOURCEMAP_JSON.read_text(encoding="utf-8"))


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
    # Direkter Zugriff auf verschachtelte .tex-Datei
    tex_path = SOURCE_DIR / project
    if not tex_path.exists():
        raise HTTPException(status_code=404, detail=f"{tex_path} not found")
    content = tex_path.read_text(encoding="utf-8")
    return {"filename": tex_path.name, "content": content}


@app.post("/save-source")
def save_source(req: SaveSourceRequest):
    safe = req.project.replace("/", "").replace("..", "")
    tex_path = SOURCE_DIR / safe / f"{safe}.tex"
    if not tex_path.exists():
        raise HTTPException(status_code=404, detail=f"{tex_path} not found")
    tex_path.write_text(req.content, encoding="utf-8")
    return {"status": "saved", "project": safe}

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





class RenameUnitRequest(BaseModel):
    oldUnitID: str
    updatedFields: dict

@app.post("/rename-unit")
def rename_unit(request: dict = Body(...)):
    import re

    if not LIB_JSON.exists() or not TOPICMAP_JSON.exists() or not SOURCEMAP_JSON.exists():
        raise HTTPException(status_code=500, detail="Required file missing")

    data = json.loads(LIB_JSON.read_text(encoding="utf-8"))
    topicmap = json.loads(TOPICMAP_JSON.read_text(encoding="utf-8"))
    sourcemap = json.loads(SOURCEMAP_JSON.read_text(encoding="utf-8"))

    try:
        old_id = request["oldUnitID"]
        updated = request["updatedFields"]
        subject = updated["Subject"]
        topic = updated.get("Topic", "")
        parent = updated.get("ParentTopic", "")
    except KeyError as e:
        raise HTTPException(status_code=400, detail="Missing required fields: " + str(e))

    old_unit = next((u for u in data if u["UnitID"] == old_id), None)
    if not old_unit:
        raise HTTPException(status_code=404, detail="Old UnitID not found")

    litid = old_unit.get("LitID")
    ctyp = old_unit.get("CTyp")
    content = old_unit.get("Content")

    try:
        topic_index = topicmap[subject]["topics"][topic]["index"]
    except KeyError:
        raise HTTPException(status_code=400, detail=f"Topic index not found for {subject} / {topic}")

    existing = [u for u in data if u["Subject"] == subject and u["LitID"] == litid and u["Topic"] == topic and u["UnitID"] != old_id]
    next_num = max([int(u["UnitID"].split("-")[-1]) for u in existing], default=0) + 1
    new_id = f"{subject}-{litid}-{topic_index:02d}-{next_num:02d}"

    # --- Update JSON
    new_unit = old_unit.copy()
    new_unit.update({
        "UnitID": new_id,
        "Subject": subject,
        "Topic": topic,
        "ParentTopic": parent,
        "TopicPath": f"{parent}/{topic}" if parent else topic
    })
    data = [u for u in data if u["UnitID"] != old_id]
    data.append(new_unit)
    LIB_JSON.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    # --- Update .tex
    tex_path = next((SOURCE_DIR / file for file, val in sourcemap.items() if val == litid), None)
    if not tex_path or not tex_path.exists():
        raise HTTPException(status_code=404, detail=f"Source file for LitID {litid} not found")

    tex = tex_path.read_text(encoding="utf-8")

    begin_block = rf"\\begin\{{{re.escape(ctyp)}\}}\{{{re.escape(old_id)}\}}\{{{re.escape(content)}\}}"
    end_block = rf"\\end\{{{re.escape(ctyp)}\}}"
    full_pattern = rf"{begin_block}(.*?){end_block}"

    match = re.search(full_pattern, tex, flags=re.DOTALL)
    if not match:
        raise HTTPException(status_code=400, detail=f"Pattern not found in .tex (Type: {ctyp}, ID: {old_id}, Content: {content})")

    body = match.group(1)
    replacement = f"\\begin{{{ctyp}}}{{{new_id}}}{{{content}}}{body}\\end{{{ctyp}}}"
    new_tex = tex[:match.start()] + replacement + tex[match.end():]
    tex_path.write_text(new_tex, encoding="utf-8")

    return {"status": "renamed", "newUnitID": new_id}

@app.post("/update-env-or-content")
def update_env_or_content(request: dict = Body(...)):
    import re

    unit_id = request.get("UnitID")
    new_content = request.get("Content")
    new_ctyp = request.get("CTyp")

    if not all([unit_id, new_content, new_ctyp]):
        raise HTTPException(status_code=400, detail="Missing UnitID, Content, or CTyp")

    if not LIB_JSON.exists() or not SOURCEMAP_JSON.exists():
        raise HTTPException(status_code=500, detail="Required files not found")

    data = json.loads(LIB_JSON.read_text(encoding="utf-8"))
    sourcemap = json.loads(SOURCEMAP_JSON.read_text(encoding="utf-8"))

    # ✅ Richtige alte Unit aus JSON lesen (nicht aus verändertem Request)
    original_unit = next((u for u in data if u["UnitID"] == unit_id), None)
    if not original_unit:
        raise HTTPException(status_code=404, detail="Unit not found")

    old_ctyp = original_unit["CTyp"]
    old_content = original_unit["Content"]

    litid = original_unit.get("LitID")
    tex_path = next((SOURCE_DIR / f for f, v in sourcemap.items() if v == litid), None)

    if not tex_path or not tex_path.exists():
        raise HTTPException(status_code=404, detail="Source file not found for LitID")

    tex = tex_path.read_text(encoding="utf-8")

    # 🔍 DEBUG-Ausgabe
    print("🧪 Alte CTyp:", old_ctyp)
    print("🧪 Alte Content:", old_content)

    pattern = (
        r"\\begin\{" + re.escape(old_ctyp) + r"\}\{" +
        re.escape(unit_id) + r"\}\{" + re.escape(old_content) + r"\}\s*\n?(.*?)\\end\{" +
        re.escape(old_ctyp) + r"\}"
    )

    print("🧪 Pattern:", pattern)

    match = re.search(pattern, tex, flags=re.DOTALL)
    if not match:
        raise HTTPException(status_code=400, detail="Pattern not found in .tex")

    body = match.group(1).strip()

    # ✅ JSON updaten
    original_unit["Content"] = new_content
    original_unit["CTyp"] = new_ctyp
    LIB_JSON.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    # 🧩 Ersatzblock erzeugen und ersetzen
    replacement = f"\\begin{{{new_ctyp}}}{{{unit_id}}}{{{new_content}}}\n{body}\n\\end{{{new_ctyp}}}"
    new_tex = tex[:match.start()] + replacement + tex[match.end():]
    tex_path.write_text(new_tex, encoding="utf-8")

    return {"status": "updated", "UnitID": unit_id}

