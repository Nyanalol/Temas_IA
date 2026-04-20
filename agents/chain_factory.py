from config import get_llm
from agents.prompts import get_extract_prompt, get_response_prompt
from agents.parsers import get_extraction_parser, get_response_parser
from agents.runnables import debug_step, get_json_cleaner, get_custom_runnable


def build_incident_chain():
    llm = get_llm()

    extract_prompt = get_extract_prompt()
    response_prompt = get_response_prompt()

    extraction_parser = get_extraction_parser()
    response_parser = get_response_parser()

    json_cleaner = get_json_cleaner()
    custom_runnable = get_custom_runnable(
        response_format_instructions=response_parser.get_format_instructions()
    )

    chain = (
        debug_step("INPUT_INITIAL")
        | extract_prompt
        | debug_step("OUTPUT_PROMPT_1")
        | llm
        | json_cleaner
        | debug_step("JSON_CLEAN_1")
        | extraction_parser
        | debug_step("PYDANTIC_OBJECT_1")
        | custom_runnable
        | debug_step("OUTPUT_CUSTOM_RUNNABLE")
        | response_prompt
        | debug_step("OUTPUT_PROMPT_2")
        | llm
        | json_cleaner
        | debug_step("JSON_CLEAN_2")
        | response_parser
        | debug_step("FINAL_PYDANTIC_OUTPUT")
    )

    return chain, extraction_parser