"""
events/api.py — API REST para crear eventos desde el iPhone (o cualquier cliente HTTP).

Arrancar:
    uvicorn events.api:app --host 0.0.0.0 --port 8000

Endpoint principal:
    POST /event
    Header: X-API-Key: <API_KEY del .env>
    Body:   {"message": "Reunión con el médico el viernes a las 10"}

Respuesta (201):
    {
      "ok": true,
      "event": {
        "title": "Médico",
        "start": "2026-04-24T10:00:00",
        "end":   "2026-04-24T11:00:00",
        ...
      }
    }
"""

import os
import secrets

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from pydantic import BaseModel

from events.chain_factory import build_event_chain
from events.icloud import create_event
from events.runnables import build_event_dict

load_dotenv()

# ── API Key ────────────────────────────────────────────────────────────────────

_API_KEY = os.getenv("API_KEY", "")
_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def _require_api_key(key: str = Security(_api_key_header)) -> str:
    if not _API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API_KEY not configured on the server.",
        )
    if not key or not secrets.compare_digest(key, _API_KEY):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key.",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    return key


# ── App ────────────────────────────────────────────────────────────────────────

app = FastAPI(title="Calendar Event API", version="1.0.0", docs_url=None, redoc_url=None)

_chain = None  # lazy init: se crea en el primer request


def _get_chain():
    global _chain
    if _chain is None:
        _chain = build_event_chain()
    return _chain


# ── Schemas ────────────────────────────────────────────────────────────────────


class EventRequest(BaseModel):
    message: str  # "Cita con el médico el viernes a las 10, 30 min, recuérdamelo antes"


class EventResponse(BaseModel):
    ok: bool
    event: dict


# ── Endpoints ──────────────────────────────────────────────────────────────────


@app.get("/health", status_code=status.HTTP_200_OK)
def health():
    """Endpoint de salud — no requiere autenticación."""
    return {"status": "ok"}


@app.post("/event", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
def create_calendar_event(
    body: EventRequest,
    _: str = Depends(_require_api_key),
):
    """
    Recibe un mensaje en lenguaje natural, extrae el evento con el LLM
    y lo crea en el calendario de iCloud configurado en .env.
    """
    try:
        extracted = _get_chain().invoke({"user_message": body.message})
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Error al extraer el evento: {exc}",
        ) from exc

    try:
        event_dict = build_event_dict(extracted)
        create_event(event_dict)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Error al crear el evento en iCloud: {exc}",
        ) from exc

    # Serializar a tipos JSON-safe (datetime → str)
    summary = {
        "title": event_dict["title"],
        "start": event_dict["start"].isoformat(),
        "end": event_dict["end"].isoformat(),
        "location": event_dict.get("location") or None,
        "notes": event_dict.get("notes") or None,
        "all_day": event_dict.get("all_day", False),
        "alarms": [
            {"minutes_before": a["trigger_minutes_before"]}
            for a in event_dict.get("alarms", [])
        ],
        "calendar": event_dict.get("calendar_name") or None,
    }

    return EventResponse(ok=True, event=summary)
