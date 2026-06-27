"""
Friday — Briefing matinal
Génère un briefing complet à partir de données réelles :
mails, calendrier, météo, RSS
"""

import requests
import anthropic
from datetime import datetime
from fastapi import APIRouter, Depends, Header, HTTPException
from typing import Optional
import xml.etree.ElementTree as ET

from config.settings import settings
from tools.dispatcher import _handle_gmail, _handle_calendar

router = APIRouter(prefix="/briefing", tags=["briefing"])


def verify_token(authorization: Optional[str] = Header(None)):
    if not authorization or authorization != f"Bearer {settings.FRIDAY_SECRET}":
        raise HTTPException(status_code=401, detail="Non autorisé")
    return True


# ─── RSS Feeds ────────────────────────────────────────────────────────────────

RSS_FEEDS = {
    "cyber": "https://feeds.feedburner.com/TheHackersNews",
    "finance": "https://www.lemonde.fr/economie/rss_full.xml",
    "geopolitique": "https://www.lemonde.fr/international/rss_full.xml",
    "politique": "https://www.lemonde.fr/politique/rss_full.xml",
}


def _fetch_rss(url: str, max_items: int = 5) -> list:
    """Récupère les titres des derniers articles d'un flux RSS"""
    try:
        r = requests.get(url, timeout=10)
        root = ET.fromstring(r.content)
        items = []
        for item in root.iter("item"):
            title = item.find("title")
            desc = item.find("description")
            if title is not None:
                items.append({
                    "title": title.text or "",
                    "description": (desc.text or "")[:200] if desc is not None else ""
                })
            if len(items) >= max_items:
                break
        return items
    except Exception as e:
        return [{"error": str(e)}]


def _fetch_weather() -> dict:
    """Météo Guérande via Open-Meteo"""
    try:
        r = requests.get(
            "https://api.open-meteo.com/v1/forecast"
            "?latitude=47.33&longitude=-2.43"
            "&current=temperature_2m,relative_humidity_2m,apparent_temperature,wind_speed_10m,weather_code"
            "&daily=temperature_2m_max,temperature_2m_min,weather_code"
            "&wind_speed_unit=kmh&timezone=Europe/Paris",
            timeout=5
        )
        d = r.json()
        c = d["current"]
        daily = d["daily"]
        wc = c["weather_code"]
        desc = (
            "Dégagé" if wc <= 1 else
            "Nuageux" if wc <= 3 else
            "Brouillard" if wc <= 48 else
            "Pluie" if wc <= 67 else
            "Neige" if wc <= 77 else
            "Orage"
        )
        return {
            "now": {
                "temp": round(c["temperature_2m"]),
                "feels_like": round(c["apparent_temperature"]),
                "humidity": c["relative_humidity_2m"],
                "wind_kmh": round(c["wind_speed_10m"]),
                "description": desc
            },
            "today": {
                "min": round(daily["temperature_2m_min"][0]),
                "max": round(daily["temperature_2m_max"][0])
            }
        }
    except Exception as e:
        return {"error": str(e)}


# ─── Endpoint principal ───────────────────────────────────────────────────────

@router.post("/generate")
def generate_briefing(_=Depends(verify_token)):
    """
    Génère le briefing matinal complet :
    - Collecte mails réels via Gmail
    - Collecte RDV réels via Calendar
    - Météo réelle via Open-Meteo
    - RSS réels
    - Demande à Claude de synthétiser
    - Sauvegarde dans le journal
    - Renvoie le briefing
    """

    # 1. Collecte des données réelles
    print("[Briefing] Collecte mails...")
    mails = _handle_gmail({"action": "list_unread", "max_results": 10})

    print("[Briefing] Collecte agenda...")
    agenda = _handle_calendar({"action": "list_today"})

    print("[Briefing] Collecte météo...")
    weather = _fetch_weather()

    print("[Briefing] Collecte RSS...")
    rss_data = {
        "cyber": _fetch_rss(RSS_FEEDS["cyber"]),
        "finance": _fetch_rss(RSS_FEEDS["finance"]),
        "geopolitique": _fetch_rss(RSS_FEEDS["geopolitique"]),
        "politique": _fetch_rss(RSS_FEEDS["politique"]),
    }

    # 2. Construction du contexte pour Claude
    today = datetime.now().strftime("%A %d %B %Y")
    mails_text = ""
    if mails.get("messages"):
        for m in mails["messages"]:
            mails_text += f"- De: {m.get('from', '?')} | Sujet: {m.get('subject', '?')}\n"
    else:
        mails_text = "Aucun mail non lu."

    agenda_text = ""
    if agenda.get("events"):
        for e in agenda["events"]:
            agenda_text += f"- {e.get('start', '?')} : {e.get('title', '?')}"
            if e.get("location"):
                agenda_text += f" ({e['location']})"
            agenda_text += "\n"
    else:
        agenda_text = "Aucun rendez-vous aujourd'hui."

    weather_text = ""
    if "now" in weather:
        w = weather["now"]
        t = weather["today"]
        weather_text = (
            f"Actuellement : {w['temp']}°C ({w['description']}), "
            f"ressenti {w['feels_like']}°C, humidité {w['humidity']}%, vent {w['wind_kmh']} km/h.\n"
            f"Aujourd'hui : min {t['min']}°C, max {t['max']}°C."
        )

    rss_text = ""
    for cat, items in rss_data.items():
        rss_text += f"\n## {cat.upper()}\n"
        for item in items[:3]:
            if "title" in item:
                rss_text += f"- {item['title']}\n"

    # 3. Génération du briefing par Claude
    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    prompt = f"""Tu es Friday, l'assistante d'Alex. Génère un briefing matinal en markdown propre, concis et factuel.

**Date : {today}**

## DONNÉES RÉELLES (utilise UNIQUEMENT ces données, n'invente rien)

### Mails non lus ({len(mails.get('messages', []))} au total)
{mails_text}

### Agenda du jour
{agenda_text}

### Météo Guérande
{weather_text}

### Actualités RSS
{rss_text}

## CONSIGNES
Structure le briefing ainsi :
# 🌅 Briefing du {today}

## 📧 Mails ({len(mails.get('messages', []))} non lus)
[Résume brièvement, signale les importants]

## 📅 Agenda
[Liste les RDV ou indique journée libre]

## 🌤️ Météo
[Météo concise]

## 📰 Actualités
### 🔐 Cybersécurité
### 💰 Finance
### 🌍 Géopolitique
### 🇫🇷 Politique française

Sois concis, factuel, et n'invente AUCUNE donnée. Si pas de données dans une section, dis-le clairement."""

    response = client.messages.create(
        model=settings.CLAUDE_MODEL,
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}]
    )
    briefing_text = "".join(b.text for b in response.content if hasattr(b, "text"))

    # 4. Sauvegarde dans le journal
    today_iso = datetime.now().strftime("%Y-%m-%d")
    try:
        requests.post(
            "http://localhost:8000/journal/",
            json={
                "type": "morning_briefing",
                "title": f"Briefing du {today}",
                "content": briefing_text
            },
            headers={"Authorization": f"Bearer {settings.FRIDAY_SECRET}"},
            timeout=5
        )
    except Exception as e:
        print(f"[Briefing] Erreur sauvegarde journal: {e}")

    # 5. Envoi notif iPhone
    try:
        ha_url = f"http://{settings.HA_HOST}:{settings.HA_PORT}/api/services/notify/mobile_app_iphone_de_alex"
        requests.post(
            ha_url,
            json={
                "message": f"Briefing du matin prêt — {len(mails.get('messages', []))} mails, {len(agenda.get('events', []))} RDV",
                "title": "FRIDAY"
            },
            headers={"Authorization": f"Bearer {settings.HA_TOKEN}"},
            timeout=5
        )
    except Exception as e:
        print(f"[Briefing] Erreur notif: {e}")

    return {
        "status": "ok",
        "date": today_iso,
        "briefing": briefing_text,
        "stats": {
            "mails_count": len(mails.get("messages", [])),
            "events_count": len(agenda.get("events", []))
        }
    }
