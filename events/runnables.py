import json
import logging
import os
import re
from datetime import datetime
from zoneinfo import ZoneInfo

from langchain_core.runnables import RunnableLambda

from .models import EventExtraction

logger = logging.getLogger(__name__)

MADRID = ZoneInfo("Europe/Madrid")
_DEFAULT_CALENDAR = os.getenv("ICLOUD_DEFAULT_CALENDAR", "Cari y Cosi")


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
        json.loads(candidate)
        logger.debug("JSON extracted with regex")
        return candidate

    raise ValueError(f"No valid JSON found in model output:\n{text}")


def _parse_dt(iso_str: str) -> datetime:
    dt = datetime.fromisoformat(iso_str)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=MADRID)
    return dt


def build_event_dict(extracted: EventExtraction) -> dict:
    logger.debug("Building event dict from: %s", extracted)

    event = {
        "title": extracted.title,
        "start": _parse_dt(extracted.start),
        "end": _parse_dt(extracted.end),
        "location": extracted.location or "",
        "notes": extracted.notes or "",
        "all_day": extracted.all_day or False,
        "repeat_freq": extracted.repeat_freq,
        "repeat_interval": extracted.repeat_interval or 1,
        "repeat_count": extracted.repeat_count,
        "repeat_until": None,
        "repeat_byday": extracted.repeat_byday,
        "categories": extracted.categories or [],
        "url": extracted.url or "",
        "status": extracted.status or "CONFIRMED",
        "transparency": extracted.transparency or "OPAQUE",
        "alarms": [],
        "calendar_name": extracted.calendar_name or _DEFAULT_CALENDAR,
    }

    if extracted.repeat_until:
        event["repeat_until"] = _parse_dt(extracted.repeat_until)

    if extracted.alarms:
        event["alarms"] = [
            {
                "action": "DISPLAY",
                "trigger_minutes_before": a.trigger_minutes_before,
                "description": a.description or extracted.title,
            }
            for a in extracted.alarms
        ]

    return event


def get_json_cleaner() -> RunnableLambda:
    return RunnableLambda(extract_json_text)
