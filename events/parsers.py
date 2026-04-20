from langchain_core.output_parsers import PydanticOutputParser

from .models import EventExtraction


def get_event_parser() -> PydanticOutputParser:
    return PydanticOutputParser(pydantic_object=EventExtraction)
