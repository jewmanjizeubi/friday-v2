"""
Friday — API principale FastAPI
"""

import base64
from fastapi import FastAPI, HTTPException, Depends, Header, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional

from core.brain import FridayBrain
from voice.voice import speech_to_text, text_to_speech
from config.settings import settings
from api.monitoring import router as monitoring_router
from api.journal_endpoint import router as journal_router
from api.presence_endpoint import router as presence_router
from api.auth import router as auth_router
from api.briefing import router as briefing_router
from api.nas import router as nas_router
app = FastAPI(title="Friday API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(monitoring_router)
app.include_router(journal_router)
app.include_router(presence_router)
app.include_router(auth_router)
app.include_router(briefing_router)
app.include_router(nas_router)

brain = FridayBrain()


# ─── Auth ─────────────────────────────────────────────────────────────────────

def verify_token(authorization: Optional[str] = Header(None)):
    if not authorization or authorization != f"Bearer {settings.FRIDAY_SECRET}":
        raise HTTPException(status_code=401, detail="Non autorisé")
    return True


# ─── Modèles ──────────────────────────────────────────────────────────────────

class TextRequest(BaseModel):
    message: str
    image_b64: Optional[str] = None

class TextResponse(BaseModel):
    response: str
    audio_b64: Optional[str] = None


# ─── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"status": "Friday is online", "version": "2.0.0"}

@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat/text", response_model=TextResponse)
async def chat_text(req: TextRequest, _=Depends(verify_token)):
    response_text = brain.think(req.message, req.image_b64)
    try:
        audio_bytes = text_to_speech(response_text)
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
    except Exception as e:
        print(f"[TTS] Erreur : {e}")
        audio_b64 = None
    return TextResponse(response=response_text, audio_b64=audio_b64)


@app.post("/chat/voice", response_model=TextResponse)
async def chat_voice(audio: UploadFile = File(...), _=Depends(verify_token)):
    audio_bytes = await audio.read()
    user_text = speech_to_text(audio_bytes)
    if not user_text:
        raise HTTPException(status_code=400, detail="Audio non reconnu")
    print(f"[STT] {user_text}")
    response_text = brain.think(user_text)
    try:
        audio_bytes = text_to_speech(response_text)
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
    except Exception:
        audio_b64 = None
    return TextResponse(response=response_text, audio_b64=audio_b64)


@app.post("/chat/vision")
async def chat_vision(
    image: UploadFile = File(...),
    question: str = "Décris ce que tu vois.",
    _=Depends(verify_token)
):
    image_bytes = await image.read()
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")
    response_text = brain.think(question, image_b64)
    try:
        audio_bytes = text_to_speech(response_text)
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
    except Exception:
        audio_b64 = None
    return {"response": response_text, "audio_b64": audio_b64}


@app.post("/conversation/reset")
async def reset_conversation(_=Depends(verify_token)):
    brain.reset_conversation()
    return {"status": "Conversation réinitialisée"}


@app.get("/memory/search")
async def search_memory(q: str, _=Depends(verify_token)):
    from tools.dispatcher import _handle_memory_search
    return _handle_memory_search({"query": q})

@app.post("/notify")
async def notify_iphone(req: TextRequest, _=Depends(verify_token)):
    """Envoie une notification directement sur l'iPhone via HA"""
    import requests as req_lib
    ha_url = f"http://{settings.HA_HOST}:{settings.HA_PORT}/api/services/notify/mobile_app_iphone_de_alex"
    headers = {
        "Authorization": f"Bearer {settings.HA_TOKEN}",
        "Content-Type": "application/json"
    }
    r = req_lib.post(ha_url, json={"message": req.message, "title": "FRIDAY"}, headers=headers, timeout=5)
    return {"success": r.status_code == 200, "status": r.status_code}

@app.get("/weather")
async def get_weather():
    """Météo via Open-Meteo (pas de clé requise) — Guérande"""
    import requests as req_lib
    try:
        r = req_lib.get(
            "https://api.open-meteo.com/v1/forecast"
            "?latitude=47.33&longitude=-2.43"
            "&current=temperature_2m,relative_humidity_2m,apparent_temperature,wind_speed_10m,weather_code"
            "&wind_speed_unit=kmh&timezone=Europe/Paris",
            timeout=5
        )
        c = r.json()["current"]
        wc = c["weather_code"]
        desc = (
            "DÉGAGÉ" if wc <= 1 else
            "NUAGEUX" if wc <= 3 else
            "BROUILLARD" if wc <= 48 else
            "PLUIE" if wc <= 67 else
            "NEIGE" if wc <= 77 else
            "ORAGE"
        )
        return {
            "main": {"temp": c["temperature_2m"], "feels_like": c["apparent_temperature"], "humidity": c["relative_humidity_2m"]},
            "wind": {"speed": c["wind_speed_10m"] / 3.6},
            "weather": [{"main": desc, "description": desc.lower()}]
        }
    except Exception as e:
        return {"error": str(e)}
