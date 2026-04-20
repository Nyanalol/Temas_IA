import json
import logging
import re

from langchain_core.runnables import RunnableLambda

from .models import IncidentExtraction

logger = logging.getLogger(__name__)


def debug_step(name: str) -> RunnableLambda:
    def _debug(x):
        logger.debug("=" * 80)
        logger.debug("STEP %s", name)
        logger.debug("%s", x)
        return x

    return RunnableLambda(_debug)


def extract_json_text(model_output):
    if hasattr(model_output, "content"):
        text = model_output.content
    else:
        text = str(model_output)

    text = text.strip()
    logger.debug("RAW_LLM_OUTPUT: %s", text)

    try:
        json.loads(text)
        logger.debug("Valid JSON detected directly")
        return text
    except Exception:
        pass

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        candidate = match.group(0)
        json.loads(candidate)
        logger.debug("Valid JSON extracted with regex: %s", candidate)
        return candidate

    raise ValueError(f"No valid JSON found in model output:\n{text}")


def build_second_stage_input(
    extracted: IncidentExtraction,
    response_format_instructions: str,
):
    logger.debug("CUSTOM_RUNNABLE_INPUT: %s", extracted)

    incident_context = (
        f"Pipeline name: {extracted.pipeline_name}\n"
        f"Dataset name: {extracted.dataset_name}\n"
        f"Layer: {extracted.layer}\n"
        f"Issue: {extracted.issue}\n"
        f"Severity: {extracted.severity}\n"
        f"Business impact: {extracted.business_impact}"
    )

    output = {
        "incident_context": incident_context,
        "format_instructions": response_format_instructions,
    }

    logger.debug("CUSTOM_RUNNABLE_OUTPUT: %s", output)
    return output


def get_json_cleaner() -> RunnableLambda:
    return RunnableLambda(extract_json_text)


def get_custom_runnable(response_format_instructions: str) -> RunnableLambda:
    def _custom(extracted: IncidentExtraction):
        return build_second_stage_input(
            extracted=extracted,
            response_format_instructions=response_format_instructions,
        )

    return RunnableLambda(_custom)
