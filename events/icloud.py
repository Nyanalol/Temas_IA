"""
icloud.py — Integración con Apple Calendar vía CalDAV.

Lee las credenciales del .env:
    ICLOUD_EMAIL
    ICLOUD_APP_PASSWORD   (app password de Apple, no la contraseña normal)
    ICLOUD_CALDAV_URL     (por defecto: https://caldav.icloud.com)
    ICLOUD_DEFAULT_CALENDAR
"""

import os
import uuid
from datetime import datetime, timezone

import caldav
from dotenv import load_dotenv

load_dotenv()

ICLOUD_EMAIL            = os.getenv("ICLOUD_EMAIL", "")
ICLOUD_APP_PASSWORD     = os.getenv("ICLOUD_APP_PASSWORD", "")
CALDAV_URL              = os.getenv("ICLOUD_CALDAV_URL", "https://caldav.icloud.com")
DEFAULT_CALENDAR_NAME   = os.getenv("ICLOUD_DEFAULT_CALENDAR", "")


# ── Helpers de formato ─────────────────────────────────────────────────────────

def _clean(value) -> str:
    if value is None:
        return ""
    text = str(value)
    text = text.replace("\\", "\\\\")
    text = text.replace("\n", "\\n")
    text = text.replace(",", "\\,")
    text = text.replace(";", "\\;")
    return text


def _fmt_utc(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _fmt_date(dt: datetime) -> str:
    return dt.strftime("%Y%m%d")


def _trigger(minutes_before: int) -> str:
    minutes_before = int(minutes_before)
    hours   = minutes_before // 60
    minutes = minutes_before % 60
    if hours and minutes:
        return f"-PT{hours}H{minutes}M"
    if hours:
        return f"-PT{hours}H"
    return f"-PT{minutes}M"


# ── Construcción del ICS ───────────────────────────────────────────────────────

def _build_valarms(event: dict) -> list[str]:
    lines = []
    for alarm in (event.get("alarms") or []):
        lines.extend([
            "BEGIN:VALARM",
            f"ACTION:{_clean(alarm.get('action', 'DISPLAY'))}",
            f"DESCRIPTION:{_clean(alarm.get('description', 'Recordatorio'))}",
            f"TRIGGER:{_trigger(alarm['trigger_minutes_before'])}",
            "END:VALARM",
        ])
    return lines


def _build_rrule(event: dict) -> str:
    freq = event.get("repeat_freq")
    if not freq:
        return ""

    valid = {"DAILY", "WEEKLY", "MONTHLY", "YEARLY"}
    if freq not in valid:
        raise ValueError(f"repeat_freq debe ser uno de {valid}")

    parts = [f"FREQ={freq}"]

    interval = event.get("repeat_interval", 1)
    if interval and interval != 1:
        parts.append(f"INTERVAL={interval}")

    if event.get("repeat_count"):
        parts.append(f"COUNT={event['repeat_count']}")

    if event.get("repeat_until"):
        parts.append(f"UNTIL={_fmt_utc(event['repeat_until'])}")

    if event.get("repeat_byday"):
        parts.append(f"BYDAY={','.join(event['repeat_byday'])}")

    return "RRULE:" + ";".join(parts)


def build_ics(event: dict) -> str:
    uid      = str(uuid.uuid4())
    now_utc  = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    all_day  = bool(event.get("all_day", False))
    title    = _clean(event["title"])
    location = _clean(event.get("location", ""))
    notes    = _clean(event.get("notes", ""))
    url      = _clean(event.get("url", ""))
    status   = _clean(event.get("status", "CONFIRMED"))
    transp   = _clean(event.get("transparency", "OPAQUE"))
    cats     = event.get("categories") or []

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:Temas_IA iCloud Agent",
        "BEGIN:VEVENT",
        f"UID:{uid}",
        f"DTSTAMP:{now_utc}",
        f"SUMMARY:{title}",
        f"STATUS:{status}",
        f"TRANSP:{transp}",
    ]

    if all_day:
        lines.append(f"DTSTART;VALUE=DATE:{_fmt_date(event['start'])}")
        lines.append(f"DTEND;VALUE=DATE:{_fmt_date(event['end'])}")
    else:
        lines.append(f"DTSTART:{_fmt_utc(event['start'])}")
        lines.append(f"DTEND:{_fmt_utc(event['end'])}")

    if location:
        lines.append(f"LOCATION:{location}")
    if notes:
        lines.append(f"DESCRIPTION:{notes}")
    if cats:
        lines.append(f"CATEGORIES:{','.join(_clean(c) for c in cats)}")
    if url:
        lines.append(f"URL:{url}")

    rrule = _build_rrule(event)
    if rrule:
        lines.append(rrule)

    lines.extend(_build_valarms(event))
    lines.extend(["END:VEVENT", "END:VCALENDAR", ""])

    return "\r\n".join(lines)


# ── Conexión y calendarios ─────────────────────────────────────────────────────

def connect_client() -> caldav.DAVClient:
    if not ICLOUD_EMAIL or not ICLOUD_APP_PASSWORD:
        raise EnvironmentError(
            "Faltan ICLOUD_EMAIL o ICLOUD_APP_PASSWORD en el .env"
        )
    clean_pwd = ICLOUD_APP_PASSWORD.replace(" ", "").replace("-", "")
    return caldav.DAVClient(url=CALDAV_URL, username=ICLOUD_EMAIL, password=clean_pwd)


def _calendar_name(cal) -> str:
    try:
        return cal.get_display_name()
    except Exception:
        return "Sin nombre"


def list_calendars(principal) -> list:
    calendars = principal.calendars()
    if not calendars:
        raise Exception("No se encontraron calendarios en iCloud")
    return calendars


def find_calendar(calendars, target_name: str):
    target = target_name.strip().lower()
    for cal in calendars:
        if _calendar_name(cal).strip().lower() == target:
            return cal
    return None


# ── Validación ────────────────────────────────────────────────────────────────

def validate_event(event: dict) -> None:
    for field in ("title", "start", "end"):
        if not event.get(field):
            raise ValueError(f"Campo obligatorio ausente: {field}")

    if not isinstance(event["start"], datetime):
        raise ValueError("start debe ser datetime")
    if not isinstance(event["end"], datetime):
        raise ValueError("end debe ser datetime")
    if event["end"] <= event["start"]:
        raise ValueError("end debe ser posterior a start")

    freq = event.get("repeat_freq")
    if freq and freq not in {"DAILY", "WEEKLY", "MONTHLY", "YEARLY"}:
        raise ValueError("repeat_freq inválido")

    status = event.get("status", "CONFIRMED")
    if status not in {"CONFIRMED", "TENTATIVE", "CANCELLED"}:
        raise ValueError("status debe ser CONFIRMED, TENTATIVE o CANCELLED")

    for alarm in (event.get("alarms") or []):
        if "trigger_minutes_before" not in alarm:
            raise ValueError("Cada alarma debe incluir trigger_minutes_before")


# ── Punto de entrada principal ─────────────────────────────────────────────────

def create_event(event: dict) -> str:
    """
    Valida y crea el evento en iCloud. Devuelve la URL del evento creado.
    """
    validate_event(event)

    client     = connect_client()
    principal  = client.principal()
    calendars  = list_calendars(principal)

    cal_name   = event.get("calendar_name") or DEFAULT_CALENDAR_NAME
    calendar   = find_calendar(calendars, cal_name)

    if calendar is None:
        available = ", ".join(_calendar_name(c) for c in calendars)
        raise Exception(
            f"Calendario '{cal_name}' no encontrado. "
            f"Disponibles: {available}"
        )

    ics_data     = build_ics(event)
    saved_event  = calendar.save_event(ics_data)

    return str(saved_event.url)
