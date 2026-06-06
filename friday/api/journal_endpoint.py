"""
Friday — Journal de bord
Stocke et expose les entrées du journal (briefings, alertes, présence...)
"""

import json
import os
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/journal", tags=["journal"])

JOURNAL_DIR = "/data/friday/journal"


def _ensure_dir():
    os.makedirs(JOURNAL_DIR, exist_ok=True)


def _journal_path(date: str) -> str:
    return os.path.join(JOURNAL_DIR, f"{date}.json")


def _load_journal(date: str) -> dict:
    path = _journal_path(date)
    if not os.path.exists(path):
        return {"date": date, "entries": [], "stats": {"events": 0, "emails": 0, "alerts": 0, "articles": 0}}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_journal(date: str, data: dict):
    _ensure_dir()
    with open(_journal_path(date), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


class JournalEntry(BaseModel):
    type: str  # morning_briefing | network_alert | presence | article | custom
    title: str
    content: str
    generated_at: Optional[str] = None
    metadata: Optional[dict] = None


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/{date}")
def get_journal(date: str):
    return _load_journal(date)


@router.get("/")
def get_today():
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return _load_journal(today)


@router.post("/{date}")
def add_entry(date: str, entry: JournalEntry):
    data = _load_journal(date)
    entry_dict = entry.dict()
    entry_dict["generated_at"] = entry.generated_at or datetime.now(timezone.utc).isoformat()
    data["entries"].append(entry_dict)

    # Mise à jour des stats
    type_map = {
        "morning_briefing": "events",
        "network_alert": "alerts",
        "article": "articles",
        "presence": "events"
    }
    stat_key = type_map.get(entry.type, "events")
    data["stats"][stat_key] = data["stats"].get(stat_key, 0) + 1

    _save_journal(date, data)
    return {"status": "ok", "entries_count": len(data["entries"])}


@router.post("/")
def add_entry_today(entry: JournalEntry):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return add_entry(today, entry)
