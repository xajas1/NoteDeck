from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import snip  # ⬅️ Stelle sicher, dass das Modul eingebunden ist

app = FastAPI()

# CORS für lokalen Zugriff vom Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # oder spezifisch: ["http://localhost:5173"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(snip.router)
