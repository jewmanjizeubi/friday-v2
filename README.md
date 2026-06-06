# FRIDAY — Personal AI Assistant

Assistant IA personnel tournant sur Raspberry Pi 5, inspiré de J.A.R.V.I.S.

## Stack

| Service | Port | Description |
|---|---|---|
| Friday API | 8000 | Backend FastAPI — cerveau de Friday |
| Friday Hub | 3000 | Interface web — nginx |
| Home Assistant | 8123 | Domotique |
| N8N | 5678 | Automatisations & briefings |
| OSINT Dashboard | 8080 | Veille & renseignement |

## Installation

### 1. Cloner le repo

```bash
git clone https://github.com/jewmanjizeubi/friday.git
cd friday
```

### 2. Configurer le .env

```bash
cp .env.example .env
nano .env  # Remplir toutes les valeurs
```

### 3. OAuth Google (Gmail + Calendar)

Sur ton PC (pas le Pi) :
```bash
pip install google-auth-oauthlib google-api-python-client
python get_google_token.py
```
Copier les valeurs `GOOGLE_*` dans `.env`.

### 4. Piper TTS

```bash
# Installer Piper
sudo apt install piper-tts

# Créer le dossier voix
mkdir -p piper-voices
# Télécharger fr_FR-siwis-medium.onnx dans piper-voices/
```

### 5. Lancer

```bash
docker compose up -d
```

## Structure

```
friday/
├── docker-compose.yml
├── .env.example
├── .gitignore
├── get_google_token.py     ← Script OAuth one-shot
├── friday/                 ← Backend FastAPI
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── api/
│   ├── core/
│   ├── config/
│   ├── tools/
│   ├── voice/
│   └── frontend/
├── nginx/
│   └── nginx.conf
├── homeassistant/
├── n8n/workflows/
├── data/                   ← Ignoré par git (runtime)
└── piper-voices/           ← Ignoré par git (trop lourd)
```

## Capacités de Friday

- 💬 Chat conversationnel avec mémoire long terme (Mem0 + ChromaDB)
- 📧 Lecture et envoi de mails (Gmail API directe)
- 📅 Gestion de l'agenda (Google Calendar API directe)
- 🏠 Contrôle domotique (Home Assistant)
- 📰 Briefing matinal automatique (N8N cron 8h)
- 🔍 Recherche OSINT
- 🎤 Voix : TTS Piper local + STT Whisper local
- 📊 Monitoring système Pi en temps réel
