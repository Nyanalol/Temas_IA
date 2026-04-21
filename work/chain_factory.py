"""
chain_factory.py — Ensambla las cadenas LCEL para cada skill del asistente de trabajo.

Cada función build_*_chain() devuelve una cadena LCEL lista para invocar
con .invoke({...}). El vectorstore del CV se carga desde disco en cada
llamada (Chroma lo cachea internamente una vez abierto).
"""

from langchain_core.runnables import RunnableLambda

from config import get_llm

from .cv_indexer import build_cv_vectorstore
from .parsers import get_cv_updater_parser, get_linkedin_optimizer_parser, get_recruiter_reply_parser
from .prompts import (
    get_cv_qa_prompt,
    get_cv_updater_prompt,
    get_linkedin_optimizer_prompt,
    get_recruiter_reply_prompt,
)
from .runnables import debug_step, format_docs, get_json_cleaner

# Caché de sesión: se carga una sola vez por ejecución del programa.
_vectorstore_cache = None


def _get_cv_context(query: str, k: int = 8, force_rebuild: bool = False) -> str:
    global _vectorstore_cache
    if force_rebuild or _vectorstore_cache is None:
        _vectorstore_cache = build_cv_vectorstore(force_rebuild=force_rebuild)
    docs = _vectorstore_cache.similarity_search(query, k=k)
    return format_docs(docs)


def invalidate_cv_cache() -> None:
    """Limpia la caché de vectorstore. Llamar tras reindexar los CVs."""
    global _vectorstore_cache
    _vectorstore_cache = None


# ── Recruiter Reply ────────────────────────────────────────────────────────────

def build_recruiter_reply_chain():
    llm = get_llm()
    parser = get_recruiter_reply_parser()
    prompt = get_recruiter_reply_prompt(parser.get_format_instructions())
    json_cleaner = get_json_cleaner()

    def enrich(inputs: dict) -> dict:
        inputs["cv_context"] = _get_cv_context(inputs.get("recruiter_message", ""))
        if not inputs.get("projects_context"):
            inputs["projects_context"] = "(No se han proporcionado proyectos actuales)"
        if not inputs.get("user_rules"):
            inputs["user_rules"] = (
                "Sé profesional y conciso. Muestra interés genuino si el rol encaja con el perfil."
            )
        return inputs

    return (
        RunnableLambda(enrich)
        | debug_step("RECRUITER_INPUT")
        | prompt
        | llm
        | json_cleaner
        | parser
        | debug_step("RECRUITER_REPLY")
    )


# ── LinkedIn Optimizer ─────────────────────────────────────────────────────────

def build_linkedin_optimizer_chain():
    llm = get_llm()
    parser = get_linkedin_optimizer_parser()
    prompt = get_linkedin_optimizer_prompt(parser.get_format_instructions())
    json_cleaner = get_json_cleaner()

    def enrich(inputs: dict) -> dict:
        query = inputs.get("linkedin_profile", "perfil profesional linkedin")
        inputs["cv_context"] = _get_cv_context(query)
        return inputs

    return (
        RunnableLambda(enrich)
        | debug_step("LINKEDIN_INPUT")
        | prompt
        | llm
        | json_cleaner
        | parser
        | debug_step("LINKEDIN_OPTIMIZATION")
    )


# ── CV Updater ─────────────────────────────────────────────────────────────────

def build_cv_updater_chain():
    llm = get_llm()
    parser = get_cv_updater_parser()
    prompt = get_cv_updater_prompt(parser.get_format_instructions())
    json_cleaner = get_json_cleaner()

    def enrich(inputs: dict) -> dict:
        instructions = inputs.get("update_instructions", "")
        # Para el CV queremos el máximo de contexto posible (k=12)
        inputs["cv_context"] = _get_cv_context(
            f"complete CV profile experience skills {instructions}", k=12
        )
        if not inputs.get("projects_context"):
            inputs["projects_context"] = "(No se han proporcionado proyectos actuales)"
        return inputs

    return (
        RunnableLambda(enrich)
        | debug_step("CV_UPDATE_INPUT")
        | prompt
        | llm
        | json_cleaner
        | parser
        | debug_step("CV_UPDATED")
    )


# ── CV Q&A ─────────────────────────────────────────────────────────────────────

def build_cv_qa_chain():
    llm = get_llm()
    prompt = get_cv_qa_prompt()

    def enrich(inputs: dict) -> dict:
        inputs["cv_context"] = _get_cv_context(inputs.get("question", ""))
        return inputs

    return (
        RunnableLambda(enrich)
        | debug_step("QA_INPUT")
        | prompt
        | llm
        | debug_step("QA_ANSWER")
    )
