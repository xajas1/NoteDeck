from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from pathlib import Path
import json


app = FastAPI(title="NoteDeck-API")

# CORS für Entwicklung aktivieren
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Für lokale Tests alles erlauben
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

LIB_JSON = Path("../Library/Library.json").resolve()

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
