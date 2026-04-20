from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class AlarmInput(BaseModel):
    trigger_minutes_before: int = Field(
        description="Minutes before the event to trigger the alarm, e.g. 10 or 30"
    )
    description: Optional[str] = Field(
        default=None,
        description="Alarm notification text. If omitted, the event title will be used.",
    )


class EventExtraction(BaseModel):
    title: str = Field(description="Short title of the event")
    start: str = Field(
        description=(
            "Event start datetime in ISO 8601 format (YYYY-MM-DDTHH:MM:SS). "
            "Resolve relative expressions like 'mañana', 'el martes' using today's date."
        )
    )
    end: str = Field(
        description=(
            "Event end datetime in ISO 8601 format. "
            "If not specified by the user, default to 1 hour after start."
        )
    )
    location: Optional[str] = Field(
        default=None, description="Physical location or address of the event"
    )
    notes: Optional[str] = Field(
        default=None, description="Additional notes or description"
    )
    all_day: Optional[bool] = Field(
        default=False, description="True only if the user explicitly says it is an all-day event"
    )
    repeat_freq: Optional[str] = Field(
        default=None,
        description="Recurrence frequency: DAILY, WEEKLY, MONTHLY, YEARLY, or null for no recurrence",
    )
    repeat_interval: Optional[int] = Field(
        default=1,
        description="Recurrence interval, e.g. 2 means every 2 weeks when repeat_freq is WEEKLY",
    )
    repeat_count: Optional[int] = Field(
        default=None, description="Total number of occurrences. Null means infinite."
    )
    repeat_until: Optional[str] = Field(
        default=None,
        description="Repeat until this date, ISO 8601 format. Null means no end date.",
    )
    repeat_byday: Optional[list[str]] = Field(
        default=None,
        description="Days of week for weekly recurrence, using two-letter codes: MO, TU, WE, TH, FR, SA, SU",
    )
    categories: Optional[list[str]] = Field(
        default=None, description="Event categories or tags, e.g. ['Salud', 'Personal']"
    )
    url: Optional[str] = Field(
        default=None, description="URL related to the event"
    )
    status: Optional[str] = Field(
        default="CONFIRMED",
        description="Event status: CONFIRMED, TENTATIVE, or CANCELLED",
    )
    transparency: Optional[str] = Field(
        default="OPAQUE",
        description="OPAQUE if the event blocks time in the calendar, TRANSPARENT if it does not",
    )
    alarms: Optional[list[AlarmInput]] = Field(
        default=None, description="List of reminders before the event"
    )
    calendar_name: Optional[str] = Field(
        default=None,
        description="Name of the target calendar. Null to use the default calendar.",
    )
