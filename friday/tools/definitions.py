"""
Définitions des outils disponibles pour Friday.
Claude lit ces définitions et décide seul lesquels appeler.
"""

TOOL_DEFINITIONS = [

    # ─── HOME ASSISTANT ───────────────────────────────────
    {
        "name": "home_assistant",
        "description": (
            "Contrôle les appareils de la maison via Home Assistant. "
            "Utilise pour : allumer/éteindre lumières, lire l'état des capteurs, "
            "contrôler les prises, volets, alarme, thermostats, etc."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["call_service", "get_state", "list_entities"],
                    "description": "Type d'action HA"
                },
                "domain": {"type": "string", "description": "Domaine HA : light, switch, cover, sensor, climate..."},
                "service": {"type": "string", "description": "Service HA : turn_on, turn_off, toggle..."},
                "entity_id": {"type": "string", "description": "ID entité HA, ex: light.salon"},
                "data": {"type": "object", "description": "Données supplémentaires (brightness, color, temperature...)"}
            },
            "required": ["action"]
        }
    },

    # ─── GMAIL ────────────────────────────────────────────
    {
        "name": "gmail",
        "description": (
            "Accès direct à Gmail via l'API Google. "
            "Utilise pour : lire les mails non lus, chercher un mail, "
            "envoyer un mail, répondre, archiver. "
            "Toujours utiliser cet outil pour toute action liée aux emails."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["list_unread", "search", "get", "send", "reply", "archive"],
                    "description": "Action à effectuer"
                },
                "query": {"type": "string", "description": "Recherche Gmail (pour action search)"},
                "message_id": {"type": "string", "description": "ID du message (pour get/reply/archive)"},
                "max_results": {"type": "integer", "description": "Nombre max de résultats (défaut: 10)"},
                "to": {"type": "string", "description": "Destinataire (pour send/reply)"},
                "subject": {"type": "string", "description": "Sujet du mail (pour send)"},
                "body": {"type": "string", "description": "Corps du mail (pour send/reply)"}
            },
            "required": ["action"]
        }
    },

    # ─── GOOGLE CALENDAR ──────────────────────────────────
    {
        "name": "google_calendar",
        "description": (
            "Accès direct à Google Calendar via l'API Google. "
            "Utilise pour : voir les événements du jour/semaine, "
            "créer un rendez-vous, modifier ou supprimer un événement. "
            "Toujours utiliser cet outil pour toute action liée à l'agenda."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["list_today", "list_week", "list_range", "create", "update", "delete"],
                    "description": "Action à effectuer"
                },
                "date_start": {"type": "string", "description": "Date début ISO 8601 (pour list_range/create)"},
                "date_end": {"type": "string", "description": "Date fin ISO 8601 (pour list_range/create)"},
                "event_id": {"type": "string", "description": "ID de l'événement (pour update/delete)"},
                "title": {"type": "string", "description": "Titre de l'événement (pour create/update)"},
                "description": {"type": "string", "description": "Description (pour create/update)"},
                "location": {"type": "string", "description": "Lieu (pour create/update)"},
                "attendees": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Liste d'emails des participants (pour create/update)"
                }
            },
            "required": ["action"]
        }
    },

    # ─── N8N WORKFLOW ─────────────────────────────────────
    {
        "name": "n8n_workflow",
        "description": (
            "Déclenche un workflow N8N pour les automatisations complexes. "
            "Utilise pour : envoyer une notification iPhone, "
            "déclencher une routine planifiée, lancer un workflow custom. "
            "Ne pas utiliser pour Gmail/Calendar — utiliser les outils dédiés."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "workflow": {
                    "type": "string",
                    "description": "Workflow à déclencher : send_notification, custom"
                },
                "payload": {"type": "object", "description": "Données à envoyer au workflow"}
            },
            "required": ["workflow"]
        }
    },

    # ─── OSINT ────────────────────────────────────────────
    {
        "name": "osint_search",
        "description": (
            "Recherche OSINT via le dashboard personnel d'Alex. "
            "Utilise pour : rechercher infos sur une personne, entreprise, "
            "domaine, IP, email. Retourne un rapport structuré."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Cible de la recherche"},
                "type": {
                    "type": "string",
                    "enum": ["person", "company", "domain", "ip", "email", "general"]
                },
                "depth": {
                    "type": "string",
                    "enum": ["quick", "standard", "deep"],
                    "description": "Profondeur de recherche (défaut: standard)"
                }
            },
            "required": ["query", "type"]
        }
    },

    # ─── MÉMOIRE ──────────────────────────────────────────
    {
        "name": "memory_search",
        "description": (
            "Recherche dans la mémoire long terme de Friday. "
            "Utilise quand Alex demande ce que Friday sait sur quelque chose, "
            "ou pour retrouver des infos d'anciennes conversations."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Ce qu'on cherche en mémoire"}
            },
            "required": ["query"]
        }
    },

    # ─── CAMÉRAS / FRIGATE ────────────────────────────────
    {
        "name": "camera_snapshot",
        "description": (
            "Snapshot d'une caméra Frigate + analyse visuelle. "
            "Utilise pour : voir ce qu'il se passe dans une pièce, "
            "vérifier la porte d'entrée, détecter une présence."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "camera_id": {"type": "string", "description": "ID caméra Frigate"},
                "question": {"type": "string", "description": "Question sur l'image"}
            },
            "required": ["camera_id", "question"]
        }
    }
]
