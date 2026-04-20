from config import get_llm

from .parsers import get_extraction_parser, get_response_parser
from .prompts import get_extract_prompt, get_response_prompt
from .runnables import debug_step, get_custom_runnable, get_json_cleaner


def build_incident_chain():
    llm = get_llm()

    extraction_parser = get_extraction_parser()
    response_parser = get_response_parser()

    extract_prompt = get_extract_prompt(extraction_parser.get_format_instructions())
    response_prompt = get_response_prompt()

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

    return chain
