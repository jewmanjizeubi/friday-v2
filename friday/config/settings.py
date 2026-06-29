"""
Friday — Configuration centralisée
Toutes les variables d'env passent par ici
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # ─── Réseau ───────────────────────────────────────────
    PI_IP: str = os.getenv("PI_IP", "192.168.1.9")
    TAILSCALE_IP: str = os.getenv("TAILSCALE_IP", "100.64.33.21")

    # ─── IA ───────────────────────────────────────────────
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    CLAUDE_MODEL: str = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")

    # ─── Mémoire ──────────────────────────────────────────
    MEMORY_PATH: str = os.getenv("MEMORY_PATH", "/data/friday/memory")

    # ─── Home Assistant ───────────────────────────────────
    HA_HOST: str = os.getenv("HA_HOST", "192.168.1.9")
    HA_PORT: int = int(os.getenv("HA_PORT", "8123"))
    HA_TOKEN: str = os.getenv("HA_TOKEN", "")
    HA_NOTIFY_SERVICE: str = os.getenv("HA_NOTIFY_SERVICE", "mobile_app_iphone_de_alex")
    HA_DEVICE_TRACKER: str = os.getenv("HA_DEVICE_TRACKER", "device_tracker.iphone_de_alex")

    # ─── Google OAuth ─────────────────────────────────────
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_REFRESH_TOKEN: str = os.getenv("GOOGLE_REFRESH_TOKEN", "")

    # ─── N8N ──────────────────────────────────────────────
    N8N_BASE_URL: str = os.getenv("N8N_BASE_URL", "http://192.168.1.9:5678")
    N8N_WEBHOOK_TOKEN: str = os.getenv("N8N_WEBHOOK_TOKEN", "")

    # ─── OSINT ────────────────────────────────────────────
    OSINT_BASE_URL: str = os.getenv("OSINT_BASE_URL", "http://localhost:8080")
    OSINT_API_KEY: str = os.getenv("OSINT_API_KEY", "")

    # ─── Frigate ──────────────────────────────────────────
    FRIGATE_HOST: str = os.getenv("FRIGATE_HOST", "localhost")
    FRIGATE_PORT: int = int(os.getenv("FRIGATE_PORT", "5000"))

    # ─── Voix ─────────────────────────────────────────────
    PIPER_MODEL: str = os.getenv("PIPER_MODEL", "/piper-voices/fr_FR-siwis-medium.onnx")
    WHISPER_MODEL: str = os.getenv("WHISPER_MODEL", "base")
    ELEVENLABS_API_KEY: str = os.getenv("ELEVENLABS_API_KEY", "")
    ELEVENLABS_VOICE_ID: str = os.getenv("ELEVENLABS_VOICE_ID", "")

    # ─── API Friday ───────────────────────────────────────
    FRIDAY_HOST: str = os.getenv("FRIDAY_HOST", "0.0.0.0")
    FRIDAY_PORT: int = int(os.getenv("FRIDAY_PORT", "8000"))
    FRIDAY_SECRET: str = os.getenv("FRIDAY_SECRET", "changez-moi")

    # ─── Hub Auth ─────────────────────────────────────────
    HUB_USERNAME: str = os.getenv("HUB_USERNAME", "alex")
    HUB_PASSWORD: str = os.getenv("HUB_PASSWORD", "changez-moi")
    HUB_SESSION_EXPIRE_HOURS: int = int(os.getenv("HUB_SESSION_EXPIRE_HOURS", "8"))

    # ─── Météo ────────────────────────────────────────────
    OPENWEATHER_API_KEY: str = os.getenv("OPENWEATHER_API_KEY", "")
    OPENWEATHER_CITY: str = os.getenv("OPENWEATHER_CITY", "Le Croisic")

    # ─── NAS Synology ─────────────────────────────────────
    NAS_HOST: str = os.getenv("NAS_HOST", "192.168.1.233")
    NAS_USERNAME: str = os.getenv("NAS_USERNAME", "")
    NAS_PASSWORD: str = os.getenv("NAS_PASSWORD", "")
settings = Settings()
