"""
Dispatcher des outils Friday.
Reçoit les appels de Claude et les route vers le bon service.
"""

import requests
import base64
import anthropic
from datetime import datetime, timezone, timedelta
from config.settings import settings


def dispatch_tool(tool_name: str, tool_input: dict) -> dict:
    """Point d'entrée unique pour tous les outils"""
    handlers = {
        "home_assistant":  _handle_home_assistant,
        "gmail":           _handle_gmail,
        "google_calendar": _handle_calendar,
        "n8n_workflow":    _handle_n8n,
        "osint_search":    _handle_osint,
        "memory_search":   _handle_memory_search,
        "camera_snapshot": _handle_camera,
    }
    handler = handlers.get(tool_name)
    if not handler:
        return {"error": f"Outil inconnu : {tool_name}"}
    try:
        return handler(tool_input)
    except Exception as e:
        return {"error": str(e)}


# ─── GOOGLE AUTH ──────────────────────────────────────────────────────────────

def _get_google_credentials():
    """Retourne des credentials Google valides via refresh token"""
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request

    creds = Credentials(
        token=None,
        refresh_token=settings.GOOGLE_REFRESH_TOKEN,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        scopes=[
            "https://www.googleapis.com/auth/gmail.modify",
            "https://www.googleapis.com/auth/calendar"
        ]
    )
    creds.refresh(Request())
    return creds


# ─── GMAIL ────────────────────────────────────────────────────────────────────

def _handle_gmail(params: dict) -> dict:
    from googleapiclient.discovery import build

    creds = _get_google_credentials()
    service = build("gmail", "v1", credentials=creds)
    action = params.get("action")

    if action == "list_unread":
        max_r = params.get("max_results", 10)
        results = service.users().messages().list(
            userId="me",
            q="is:unread category:primary",
            maxResults=max_r
        ).execute()
        messages = results.get("messages", [])
        summaries = []
        for msg in messages:
            m = service.users().messages().get(
                userId="me", id=msg["id"], format="metadata",
                metadataHeaders=["From", "Subject", "Date"]
            ).execute()
            headers = {h["name"]: h["value"] for h in m["payload"]["headers"]}
            summaries.append({
                "id": msg["id"],
                "from": headers.get("From", ""),
                "subject": headers.get("Subject", ""),
                "date": headers.get("Date", ""),
                "snippet": m.get("snippet", "")
            })
        return {"unread_count": len(summaries), "messages": summaries}

    elif action == "search":
        query = params.get("query", "")
        max_r = params.get("max_results", 10)
        results = service.users().messages().list(
            userId="me", q=query, maxResults=max_r
        ).execute()
        messages = results.get("messages", [])
        summaries = []
        for msg in messages:
            m = service.users().messages().get(
                userId="me", id=msg["id"], format="metadata",
                metadataHeaders=["From", "Subject", "Date"]
            ).execute()
            headers = {h["name"]: h["value"] for h in m["payload"]["headers"]}
            summaries.append({
                "id": msg["id"],
                "from": headers.get("From", ""),
                "subject": headers.get("Subject", ""),
                "date": headers.get("Date", ""),
                "snippet": m.get("snippet", "")
            })
        return {"results": summaries}

    elif action == "get":
        msg_id = params.get("message_id")
        m = service.users().messages().get(
            userId="me", id=msg_id, format="full"
        ).execute()
        headers = {h["name"]: h["value"] for h in m["payload"]["headers"]}
        # Extraction du corps
        body = ""
        if "parts" in m["payload"]:
            for part in m["payload"]["parts"]:
                if part["mimeType"] == "text/plain":
                    body = base64.urlsafe_b64decode(
                        part["body"]["data"].encode()
                    ).decode("utf-8", errors="replace")
                    break
        elif "body" in m["payload"] and m["payload"]["body"].get("data"):
            body = base64.urlsafe_b64decode(
                m["payload"]["body"]["data"].encode()
            ).decode("utf-8", errors="replace")
        return {
            "id": msg_id,
            "from": headers.get("From", ""),
            "subject": headers.get("Subject", ""),
            "date": headers.get("Date", ""),
            "body": body[:3000]
        }

    elif action == "send":
        import email.mime.text
        import email.mime.multipart
        msg = email.mime.multipart.MIMEMultipart()
        msg["To"] = params.get("to", "")
        msg["Subject"] = params.get("subject", "")
        msg.attach(email.mime.text.MIMEText(params.get("body", ""), "plain"))
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        service.users().messages().send(
            userId="me", body={"raw": raw}
        ).execute()
        return {"success": True, "to": params.get("to"), "subject": params.get("subject")}

    elif action == "archive":
        service.users().messages().modify(
            userId="me", id=params.get("message_id"),
            body={"removeLabelIds": ["INBOX"]}
        ).execute()
        return {"success": True}

    return {"error": f"Action Gmail inconnue : {action}"}


# ─── GOOGLE CALENDAR ──────────────────────────────────────────────────────────

def _handle_calendar(params: dict) -> dict:
    from googleapiclient.discovery import build

    creds = _get_google_credentials()
    service = build("calendar", "v3", credentials=creds)
    action = params.get("action")

    def _format_event(e):
        start = e.get("start", {})
        end = e.get("end", {})
        return {
            "id": e.get("id"),
            "title": e.get("summary", ""),
            "start": start.get("dateTime", start.get("date", "")),
            "end": end.get("dateTime", end.get("date", "")),
            "location": e.get("location", ""),
            "description": e.get("description", ""),
            "attendees": [a.get("email") for a in e.get("attendees", [])]
        }

    if action in ("list_today", "list_week"):
        now = datetime.now(timezone.utc)
        time_min = now.replace(hour=0, minute=0, second=0).isoformat()
        if action == "list_today":
            time_max = now.replace(hour=23, minute=59, second=59).isoformat()
        else:
            time_max = (now + timedelta(days=7)).isoformat()
        events = service.events().list(
            calendarId="primary",
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy="startTime"
        ).execute()
        return {"events": [_format_event(e) for e in events.get("items", [])]}

    elif action == "list_range":
        events = service.events().list(
            calendarId="primary",
            timeMin=params.get("date_start"),
            timeMax=params.get("date_end"),
            singleEvents=True,
            orderBy="startTime"
        ).execute()
        return {"events": [_format_event(e) for e in events.get("items", [])]}

    elif action == "create":
        body = {
            "summary": params.get("title", ""),
            "description": params.get("description", ""),
            "location": params.get("location", ""),
            "start": {"dateTime": params.get("date_start"), "timeZone": "Europe/Paris"},
            "end": {"dateTime": params.get("date_end"), "timeZone": "Europe/Paris"},
        }
        if params.get("attendees"):
            body["attendees"] = [{"email": a} for a in params["attendees"]]
        event = service.events().insert(calendarId="primary", body=body).execute()
        return {"success": True, "event": _format_event(event)}

    elif action == "update":
        event = service.events().get(
            calendarId="primary", eventId=params.get("event_id")
        ).execute()
        if params.get("title"):
            event["summary"] = params["title"]
        if params.get("description"):
            event["description"] = params["description"]
        if params.get("date_start"):
            event["start"] = {"dateTime": params["date_start"], "timeZone": "Europe/Paris"}
        if params.get("date_end"):
            event["end"] = {"dateTime": params["date_end"], "timeZone": "Europe/Paris"}
        updated = service.events().update(
            calendarId="primary", eventId=params.get("event_id"), body=event
        ).execute()
        return {"success": True, "event": _format_event(updated)}

    elif action == "delete":
        service.events().delete(
            calendarId="primary", eventId=params.get("event_id")
        ).execute()
        return {"success": True}

    return {"error": f"Action Calendar inconnue : {action}"}


# ─── HOME ASSISTANT ───────────────────────────────────────────────────────────

def _handle_home_assistant(params: dict) -> dict:
    action = params.get("action")
    base = f"http://{settings.HA_HOST}:{settings.HA_PORT}"
    headers = {
        "Authorization": f"Bearer {settings.HA_TOKEN}",
        "Content-Type": "application/json"
    }

    if action == "list_entities":
        r = requests.get(f"{base}/api/states", headers=headers, timeout=5)
        entities = [{"id": e["entity_id"], "state": e["state"]} for e in r.json()]
        return {"entities": entities}

    elif action == "get_state":
        entity_id = params.get("entity_id")
        r = requests.get(f"{base}/api/states/{entity_id}", headers=headers, timeout=5)
        data = r.json()
        return {
            "entity_id": entity_id,
            "state": data.get("state"),
            "attributes": data.get("attributes", {})
        }

    elif action == "call_service":
        domain = params.get("domain")
        service = params.get("service")
        payload = {"entity_id": params.get("entity_id")}
        if params.get("data"):
            payload.update(params["data"])
        r = requests.post(
            f"{base}/api/services/{domain}/{service}",
            headers=headers, json=payload, timeout=5
        )
        return {"success": r.status_code == 200, "status": r.status_code}

    return {"error": "Action HA inconnue"}


# ─── N8N ──────────────────────────────────────────────────────────────────────

def _handle_n8n(params: dict) -> dict:
    workflow = params.get("workflow")
    payload = params.get("payload", {})

    webhook_map = {
        "send_notification": f"{settings.N8N_BASE_URL}/webhook/friday-notify",
        "custom":            f"{settings.N8N_BASE_URL}/webhook/friday-custom",
    }

    url = webhook_map.get(workflow)
    if not url:
        return {"error": f"Workflow N8N inconnu : {workflow}"}

    headers = {"Authorization": f"Bearer {settings.N8N_WEBHOOK_TOKEN}"}
    r = requests.post(url, json=payload, headers=headers, timeout=15)
    try:
        return r.json()
    except Exception:
        return {"status": r.status_code, "raw": r.text[:500]}


# ─── OSINT ────────────────────────────────────────────────────────────────────

def _handle_osint(params: dict) -> dict:
    url = f"{settings.OSINT_BASE_URL}/api/search"
    headers = {"Authorization": f"Bearer {settings.OSINT_API_KEY}"}
    r = requests.post(url, json=params, headers=headers, timeout=30)
    try:
        return r.json()
    except Exception:
        return {"status": r.status_code, "raw": r.text[:1000]}


# ─── MÉMOIRE ──────────────────────────────────────────────────────────────────

def _handle_memory_search(params: dict) -> dict:
    from mem0 import Memory
    mem = Memory.from_config({
        "vector_store": {
            "provider": "chroma",
            "config": {
                "collection_name": "friday_memory",
                "path": settings.MEMORY_PATH
            }
        }
    })
    results = mem.search(params.get("query"), user_id="alex", limit=8)
    return {"memories": [r["memory"] for r in results]}


# ─── CAMÉRA / FRIGATE ─────────────────────────────────────────────────────────

def _handle_camera(params: dict) -> dict:
    camera_id = params.get("camera_id")
    question = params.get("question", "Décris ce que tu vois.")

    frigate_url = f"http://{settings.FRIGATE_HOST}:{settings.FRIGATE_PORT}/api/{camera_id}/latest.jpg"
    r = requests.get(frigate_url, timeout=5)
    if r.status_code != 200:
        return {"error": f"Impossible de récupérer la caméra {camera_id}"}

    image_b64 = base64.b64encode(r.content).decode("utf-8")

    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    response = client.messages.create(
        model=settings.CLAUDE_MODEL,
        max_tokens=512,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": image_b64}},
                {"type": "text", "text": question}
            ]
        }]
    )
    return {"analysis": response.content[0].text, "camera": camera_id}
