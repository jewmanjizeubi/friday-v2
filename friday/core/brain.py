"""
FRIDAY — Cerveau central
Gère la conversation, la mémoire, et le dispatch des outils
"""

import json
import base64
import anthropic
from mem0 import Memory
from typing import Optional
from config.settings import settings
from tools.dispatcher import dispatch_tool
from tools.definitions import TOOL_DEFINITIONS

# ─── Init clients ─────────────────────────────────────────────────────────────

client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

memory = Memory.from_config({
    "vector_store": {
        "provider": "chroma",
        "config": {
            "collection_name": "friday_memory",
            "path": settings.MEMORY_PATH
        }
    },
    "embedder": {
        "provider": "huggingface",
        "config": {"model": "sentence-transformers/all-MiniLM-L6-v2"}
    },
    "llm": {
        "provider": "anthropic",
        "config": {
            "model": "claude-haiku-4-5-20251001",
            "api_key": settings.ANTHROPIC_API_KEY
        }
    }
})

SYSTEM_PROMPT = """Tu es Friday, l'assistante IA personnelle d'Alex.
Tu es intelligente, directe, légèrement sarcastique mais toujours bienveillante.
Tu t'exprimes en français sauf si on te parle dans une autre langue.
Tu as accès à la maison, aux mails, au calendrier, aux workflows et à la mémoire d'Alex.

Règles fondamentales :
- Tu n'appelles un outil QUE si c'est nécessaire. Sinon tu réponds directement.
- Pour tout ce qui concerne les mails : utilise l'outil gmail directement.
- Pour tout ce qui concerne l'agenda : utilise l'outil google_calendar directement.
- Tu es proactive : si tu remarques quelque chose d'important, tu le signales.
- Tu te souviens de tout ce qu'Alex te dit. Tu utilises ces infos naturellement.
- Tu es concise. Pas de blabla inutile.
- Quand tu crées un événement avec des participants, propose d'envoyer un mail pour les prévenir.

Tu tournes localement sur le Raspberry Pi 5 d'Alex."""


class FridayBrain:
    def __init__(self):
        self.conversation_history = []
        self.user_id = "alex"

    def _get_memory_context(self, query: str) -> str:
        try:
            memories = memory.search(query, user_id=self.user_id, limit=5)
            if not memories:
                return ""
            return "\n".join(f"- {m['memory']}" for m in memories)
        except Exception:
            return ""

    def _save_to_memory(self, user_msg: str, assistant_msg: str):
        try:
            memory.add(
                f"Utilisateur: {user_msg}\nFriday: {assistant_msg}",
                user_id=self.user_id
            )
        except Exception:
            pass

    def _build_messages(self, user_input: str, image_b64: Optional[str] = None):
        mem_context = self._get_memory_context(user_input)
        system = SYSTEM_PROMPT
        if mem_context:
            system += f"\n\nMémoire long terme sur Alex :\n{mem_context}"

        if image_b64:
            user_content = [
                {
                    "type": "image",
                    "source": {"type": "base64", "media_type": "image/jpeg", "data": image_b64}
                },
                {"type": "text", "text": user_input}
            ]
        else:
            user_content = user_input

        messages = self.conversation_history + [{"role": "user", "content": user_content}]
        return system, messages

    def think(self, user_input: str, image_b64: Optional[str] = None) -> str:
        system, messages = self._build_messages(user_input, image_b64)

        response = client.messages.create(
            model=settings.CLAUDE_MODEL,
            max_tokens=1024,
            system=system,
            tools=TOOL_DEFINITIONS,
            messages=messages
        )

        # Boucle ReAct : tool use → résultat → reformulation
        while response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    print(f"[Friday] Outil : {block.name} — {block.input}")
                    result = dispatch_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result, ensure_ascii=False)
                    })

            messages = messages + [
                {"role": "assistant", "content": response.content},
                {"role": "user", "content": tool_results}
            ]

            response = client.messages.create(
                model=settings.CLAUDE_MODEL,
                max_tokens=1024,
                system=system,
                tools=TOOL_DEFINITIONS,
                messages=messages
            )

        # Extraction réponse finale
        final_text = "".join(
            block.text for block in response.content if hasattr(block, "text")
        )

        # Historique conversation (10 échanges max)
        self.conversation_history.append({"role": "user", "content": user_input})
        self.conversation_history.append({"role": "assistant", "content": final_text})
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]

        self._save_to_memory(user_input, final_text)
        return final_text

    def reset_conversation(self):
        self.conversation_history = []
