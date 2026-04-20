"""
config.py — Punto central de configuración de LLMs y embeddings.

En lugar de instanciar el LLM directamente en cada script, todos
importan get_llm() y get_embeddings() desde aquí. Así, para cambiar
de proveedor basta con editar el .env, sin tocar el código.

Las importaciones son lazy: solo se importa el paquete del proveedor
activo, de modo que no necesitas tener instalados todos si usas uno solo.

Proveedores soportados
  LLM        : ollama | openai | anthropic | groq
  Embeddings : ollama | openai
"""

import os

from dotenv import load_dotenv

load_dotenv()

# ── Variables leídas del .env (con valores por defecto para Ollama) ────────────

LLM_PROVIDER    = os.getenv("LLM_PROVIDER",    "ollama")
LLM_MODEL       = os.getenv("LLM_MODEL",       "llama3")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0"))

EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "ollama")
EMBEDDING_MODEL    = os.getenv("EMBEDDING_MODEL",    "nomic-embed-text")


# ──────────────────────────────────────────────────────────────────────────────

def get_llm():
    """Devuelve una instancia del LLM configurado en .env."""

    print(f"[config] LLM → proveedor={LLM_PROVIDER}  modelo={LLM_MODEL}")

    if LLM_PROVIDER == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(model=LLM_MODEL, temperature=LLM_TEMPERATURE)

    if LLM_PROVIDER == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=LLM_MODEL,
            temperature=LLM_TEMPERATURE,
            api_key=os.getenv("OPENAI_API_KEY"),  # type: ignore[arg-type]
        )

    if LLM_PROVIDER == "anthropic":
        try:
            from langchain_anthropic import ChatAnthropic
        except ImportError:
            raise ImportError(
                "El paquete 'langchain-anthropic' no está instalado. "
                "Ejecuta: uv add langchain-anthropic"
            )
        return ChatAnthropic(
            model=LLM_MODEL,  # type: ignore[call-arg]
            temperature=LLM_TEMPERATURE,
            api_key=os.getenv("ANTHROPIC_API_KEY"),  # type: ignore[arg-type]
        )

    if LLM_PROVIDER == "groq":
        try:
            from langchain_groq import ChatGroq
        except ImportError:
            raise ImportError(
                "El paquete 'langchain-groq' no está instalado. "
                "Ejecuta: uv add langchain-groq"
            )
        return ChatGroq(
            model=LLM_MODEL,
            temperature=LLM_TEMPERATURE,
            api_key=os.getenv("GROQ_API_KEY"),  # type: ignore[arg-type]
        )

    raise ValueError(
        f"[config] LLM_PROVIDER desconocido: '{LLM_PROVIDER}'. "
        "Opciones válidas: ollama | openai | anthropic | groq"
    )


def get_embeddings():
    """Devuelve una instancia del modelo de embeddings configurado en .env."""

    print(f"[config] Embeddings → proveedor={EMBEDDING_PROVIDER}  modelo={EMBEDDING_MODEL}")

    if EMBEDDING_PROVIDER == "ollama":
        from langchain_ollama import OllamaEmbeddings
        return OllamaEmbeddings(model=EMBEDDING_MODEL)

    if EMBEDDING_PROVIDER == "openai":
        from langchain_openai import OpenAIEmbeddings
        return OpenAIEmbeddings(
            model=EMBEDDING_MODEL,
            api_key=os.getenv("OPENAI_API_KEY"),  # type: ignore[arg-type]
        )

    raise ValueError(
        f"[config] EMBEDDING_PROVIDER desconocido: '{EMBEDDING_PROVIDER}'. "
        "Opciones válidas: ollama | openai"
    )
