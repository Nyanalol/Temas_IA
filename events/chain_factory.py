from config import get_llm

from .parsers import get_event_parser
from .prompts import get_extract_prompt
from .runnables import debug_step, get_json_cleaner


def build_event_chain():
    llm = get_llm()
    parser = get_event_parser()
    prompt = get_extract_prompt(parser.get_format_instructions())
    json_cleaner = get_json_cleaner()

    chain = (
        debug_step("INPUT")
        | prompt
        | debug_step("PROMPT")
        | llm
        | json_cleaner
        | debug_step("JSON_CLEAN")
        | parser
        | debug_step("EXTRACTED_EVENT")
    )

    return chain
