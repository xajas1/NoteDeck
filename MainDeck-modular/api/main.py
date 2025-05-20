from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Request
from pathlib import Path
import json
import subprocess
import os

app = FastAPI(title="NoteDeck-API")

# CORS für Entwicklung aktivieren
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Für lokale Tests alles erlauben
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR       = Path(__file__).resolve().parents[1]
LIB_JSON       = BASE_DIR / "Library" / "Library.json"
EXPORT_DIR     = BASE_DIR / "Export"
EXPORT_SCRIPT  = Path("export_builder.py").resolve()


def load_units():
    if not LIB_JSON.exists():
        return []
    return json.loads(LIB_JSON.read_text(encoding="utf-8"))

@app.get("/units")
def get_units(subject: str | None = None,
              topic: str | None = None,
              layer: int  | None = None,
              comp:  int  | None = None):
    """Liefert alle Units, optional gefiltert."""
    data = load_units()
    def match(u):
        return ((subject is None or u["Subject"] == subject) and
                (topic   is None or u["Topic"]   == topic)   and
                (layer   is None or str(u.get("Layer")) == str(layer)) and
                (comp    is None or str(u.get("Comp"))  == str(comp)))
    return [u for u in data if match(u)]


@app.post("/export-project/{project_name}")
async def backup_project_only_json(project_name: str, request: Request):
    """🧠 Nur JSON-Struktur sichern. Kein .tex Export."""
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
    """📄 Rufe das Tex-Erzeugungs-Skript auf."""
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
