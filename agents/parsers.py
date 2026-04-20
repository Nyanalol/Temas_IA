from langchain_core.output_parsers import PydanticOutputParser
from pydantic_test import IncidentExtraction, IncidentResponse


def get_extraction_parser() -> PydanticOutputParser:
    return PydanticOutputParser(pydantic_object=IncidentExtraction)


def get_response_parser() -> PydanticOutputParser:
    return PydanticOutputParser(pydantic_object=IncidentResponse)