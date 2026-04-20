import json
import re
from langchain_core.runnables import RunnableLambda
from pydantic_test import IncidentExtraction


def print_title(title: str) -> None:
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def debug_step(name: str) -> RunnableLambda:
    def _debug(x):
        print_title(f"STEP {name}")
        print(x)
        return x

    return RunnableLambda(_debug)


def extract_json_text(model_output):
    print_title("STEP RAW_LLM_OUTPUT")

    if hasattr(model_output, "content"):
        text = model_output.content
    else:
        text = str(model_output)

    print(text)
    text = text.strip()

    print_title("STEP JSON_CLEANER")

    try:
        json.loads(text)
        print("Valid JSON detected directly")
        return text
    except Exception:
        pass

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        candidate = match.group(0)
        json.loads(candidate)
        print("Valid JSON extracted with regex")
        print(candidate)
        return candidate

    raise ValueError(f"No valid JSON found in model output:\n{text}")


def build_second_stage_input(
    extracted: IncidentExtraction,
    response_format_instructions: str,
):
    print_title("STEP CUSTOM_RUNNABLE_INPUT")
    print(extracted)

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

    print_title("STEP CUSTOM_RUNNABLE_OUTPUT")
    print(output)

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