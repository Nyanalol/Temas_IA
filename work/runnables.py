"""
runnables.py — Transformaciones LCEL compartidas para el asistente de trabajo.

Replica el patrón de debug_step / json_cleaner ya establecido en events/.
"""

import json
import logging
import re

from langchain_core.runnables import RunnableLambda

logger = logging.getLogger(__name__)


def debug_step(name: str) -> RunnableLambda:
    def _debug(x):
        logger.debug("=" * 60)
        logger.debug("STEP %s", name)
        logger.debug("%s", x)
        return x

    return RunnableLambda(_debug)


def extract_json_text(model_output) -> str:
    text = model_output.content if hasattr(model_output, "content") else str(model_output)
    text = text.strip()
    logger.debug("RAW_LLM_OUTPUT: %s", text)

    try:
        json.loads(text)
        return text
    except Exception:
        pass

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        candidate = match.group(0)
        try:
            json.loads(candidate)
            logger.debug("JSON extracted with regex")
            return candidate
        except Exception:
            pass

    raise ValueError(f"No valid JSON found in model output:\n{text}")


def format_docs(docs) -> str:
    """Formatea una lista de Documents en texto plano para el contexto del LLM."""
    return "\n\n".join(doc.page_content for doc in docs)


def get_json_cleaner() -> RunnableLambda:
    return RunnableLambda(extract_json_text)
