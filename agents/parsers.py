from langchain_core.output_parsers import PydanticOutputParser
from .models import IncidentExtraction, IncidentResponse


def get_extraction_parser() -> PydanticOutputParser:
    return PydanticOutputParser(pydantic_object=IncidentExtraction)


def get_response_parser() -> PydanticOutputParser:
    return PydanticOutputParser(pydantic_object=IncidentResponse)