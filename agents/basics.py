"""
basics.py — Introducción a los tipos de mensaje y agentes con LangChain.

En LangChain los mensajes tienen roles:
  SystemMessage  → instrucciones globales al modelo (personalidad, restricciones…)
  HumanMessage   → lo que dice el usuario
  AIMessage      → la respuesta del modelo (útil para mantener historial)

El LLM se obtiene de config.py para no repetir la inicialización aquí.

Ejecución (desde la raíz del proyecto):
    python agents/basics.py
"""

import sys
from pathlib import Path

# Añadimos la raíz al path para poder importar config.py.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config import get_llm
from langchain_core.messages import SystemMessage, HumanMessage


# ── Configuración ──────────────────────────────────────────────────────────────

llm = get_llm()

QUERY = "Dame el ejemplo de registro de log en mis documentos"


# ── Ejemplo básico de mensajes ─────────────────────────────────────────────────

messages = [
    SystemMessage(content="Eres un asistente técnico experto en desarrollo de software."),
    HumanMessage(content=QUERY),
]

print(f"\n[agents] Enviando query: {QUERY}")

response = llm.invoke(messages)

print("\n[agents] Respuesta:")
print(response.content)
