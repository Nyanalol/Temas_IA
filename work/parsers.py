"""
parsers.py — Pydantic output parsers para cada skill del asistente de trabajo.
"""

from langchain_core.output_parsers import PydanticOutputParser

from .models import CVDocument, LinkedInOptimization, RecruiterReply


def get_recruiter_reply_parser() -> PydanticOutputParser:
    return PydanticOutputParser(pydantic_object=RecruiterReply)


def get_linkedin_optimizer_parser() -> PydanticOutputParser:
    return PydanticOutputParser(pydantic_object=LinkedInOptimization)


def get_cv_updater_parser() -> PydanticOutputParser:
    return PydanticOutputParser(pydantic_object=CVDocument)
