"""
Friday — Présence
Webhooks HA pour détecter arrivée/départ d'Alex
"""

from datetime import datetime, timezone
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/presence", tags=["presence"])

_presence_state = {
    "home": False,
    "last_seen": None,
    "last_event": None
}


class PresenceEvent(BaseModel):
    event: str  # "arrived" | "left"
    person: str = "alex"
    timestamp: str = None


@router.post("/webhook")
def presence_webhook(event: PresenceEvent):
    ts = event.timestamp or datetime.now(timezone.utc).isoformat()
    _presence_state["home"] = event.event == "arrived"
    _presence_state["last_seen"] = ts
    _presence_state["last_event"] = event.event

    # Log dans le journal
    try:
        import httpx
        entry = {
            "type": "presence",
            "title": f"Alex {'est arrivé' if event.event == 'arrived' else 'est parti'}",
            "content": f"Événement de présence : {event.event} à {ts}",
            "generated_at": ts
        }
        httpx.post("http://localhost:8000/journal/", json=entry, timeout=3)
    except Exception:
        pass

    return {"status": "ok", "state": _presence_state}


@router.get("/state")
def get_presence():
    return _presence_state
