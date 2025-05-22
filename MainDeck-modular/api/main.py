from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
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

# Basisverzeichnisse
BASE_DIR       = Path(__file__).resolve().parents[1]
LIB_JSON       = BASE_DIR / "Library" / "Library.json"
EXPORT_DIR     = BASE_DIR / "Export"
EXPORT_SCRIPT  = Path("export_builder.py").resolve()


# ----------------------------- Units laden -----------------------------

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


# ----------------------------- Export JSON -----------------------------

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


# ----------------------------- Export TeX -----------------------------

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


# ----------------------------- Live Compile Endpoint -----------------------------

@app.post("/compile")
async def compile_tex(request: Request):
    """🧪 Kompiliert LaTeX-Code und gibt PDF zurück."""
    try:
        data = await request.json()
        tex_code = data.get("tex", "")
        if not tex_code.strip():
            return {"error": "⚠️ Kein LaTeX-Code übergeben."}

        tmp_dir = Path("/tmp/tex_compile")
        tmp_dir.mkdir(parents=True, exist_ok=True)

        tex_file = tmp_dir / "temp.tex"
        tex_file.write_text(tex_code, encoding="utf-8")

        subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", tex_file.name],
            cwd=tmp_dir,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        pdf_file = tex_file.with_suffix(".pdf")
        if not pdf_file.exists():
            return {"error": "❌ PDF wurde nicht generiert."}

        return FileResponse(str(pdf_file), media_type="application/pdf")

    except subprocess.CalledProcessError as e:
        return {"error": "❌ Kompilierungsfehler", "details": e.stderr.decode(errors='ignore')}

    except Exception as e:
        return {"error": "❌ Serverfehler", "message": str(e)}
