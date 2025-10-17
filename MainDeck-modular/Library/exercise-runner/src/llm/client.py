# src/llm/client.py
import os
from dotenv import load_dotenv
from openai import OpenAI

# .env laden (OPENAI_API_KEY, SOLVE_MODEL, CRITIC_MODEL, REFINE_MODEL)
load_dotenv()

def get_client() -> OpenAI:
    """Erzeuge einen OpenAI-Client aus dem .env-API-Key."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY fehlt in .env")
    return OpenAI(api_key=api_key)

def get_model(kind: str, default: str) -> str:
    """
    Lies den Modellnamen aus .env, z.B. kind='solve' -> SOLVE_MODEL.
    Fällt auf 'default' zurück, wenn nicht gesetzt.
    """
    return os.getenv(f"{kind.upper()}_MODEL", default)
