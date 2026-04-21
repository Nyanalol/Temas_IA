"""
Entry point del agente de calendario.

Uso:
    python -m events.main

El agente acepta lenguaje natural y crea eventos en Apple Calendar (iCloud).
Ejemplos:
    "Cita con el médico el viernes a las 9, duración 30 minutos, recuérdamelo 15 minutos antes"
    "Reunión de equipo todos los lunes a las 10, sin fin, con recordatorio de 10 y 30 minutos"
    "Cumpleaños de María el 5 de mayo, todo el día"
"""

import logging
import os
import subprocess
import time
import urllib.request

from dotenv import load_dotenv

from events.chain_factory import build_event_chain
from events.icloud import create_event
from events.runnables import build_event_dict

load_dotenv()

logging.basicConfig(
    level=logging.WARNING,
    format="%(name)s | %(levelname)s | %(message)s",
)
logging.getLogger("events").setLevel(logging.DEBUG)


def _ensure_ollama_running(timeout: int = 15) -> None:
    url = "http://127.0.0.1:11434"
    try:
        urllib.request.urlopen(url, timeout=2)
        return
    except Exception:
        pass

    print("Ollama no está arrancado, iniciando...")
    subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            urllib.request.urlopen(url, timeout=2)
            print("Ollama listo.\n")
            return
        except Exception:
            time.sleep(1)

    raise RuntimeError(f"Ollama no arrancó en {timeout}s. Comprueba la instalación.")


def _show_event_summary(extracted) -> None:
    print("\n" + "─" * 60)
    print("  EVENTO EXTRAÍDO")
    print("─" * 60)
    print(f"  Título       : {extracted.title}")
    print(f"  Inicio       : {extracted.start}")
    print(f"  Fin          : {extracted.end}")
    if extracted.location:
        print(f"  Lugar        : {extracted.location}")
    if extracted.notes:
        print(f"  Notas        : {extracted.notes}")
    if extracted.all_day:
        print("  Todo el día  : Sí")
    if extracted.repeat_freq:
        print(f"  Repetición   : {extracted.repeat_freq} (cada {extracted.repeat_interval})")
        if extracted.repeat_byday:
            print(f"  Días         : {', '.join(extracted.repeat_byday)}")
        if extracted.repeat_count:
            print(f"  N.º veces    : {extracted.repeat_count}")
        if extracted.repeat_until:
            print(f"  Hasta        : {extracted.repeat_until}")
    if extracted.alarms:
        reminders = ", ".join(f"{a.trigger_minutes_before} min" for a in extracted.alarms)
        print(f"  Recordatorios: {reminders}")
    if extracted.categories:
        print(f"  Categorías   : {', '.join(extracted.categories)}")
    if extracted.calendar_name:
        print(f"  Calendario   : {extracted.calendar_name}")
    print("─" * 60)


def main() -> None:
    if os.getenv("LLM_PROVIDER", "ollama").lower() == "ollama":
        _ensure_ollama_running()
    chain = build_event_chain()

    print("=" * 60)
    print("  Agente de Calendario — iCloud")
    print("  Escribe 'salir' para terminar")
    print("=" * 60)

    while True:
        try:
            user_input = input("\nTú: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nHasta luego.")
            break

        if not user_input:
            continue
        if user_input.lower() in ("salir", "exit", "quit"):
            print("Hasta luego.")
            break

        # ── Extracción ──────────────────────────────────────────────────────
        try:
            extracted = chain.invoke({"user_message": user_input})
        except Exception as exc:
            print(f"\n[Error al extraer el evento] {exc}")
            print("Intenta ser más específico con la fecha y hora.")
            continue

        _show_event_summary(extracted)

        # ── Confirmación ────────────────────────────────────────────────────
        try:
            confirm = input("\n¿Crear este evento? [s/N]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nCancelado.")
            break

        if confirm not in ("s", "si", "sí", "y", "yes"):
            print("Evento descartado.")
            continue

        # ── Creación en iCloud ───────────────────────────────────────────────
        try:
            event_dict = build_event_dict(extracted)
            url = create_event(event_dict)
            print("\nEvento creado correctamente.")
            print(f"URL: {url}")
        except Exception as exc:
            print(f"\n[Error al crear el evento en iCloud] {exc}")


if __name__ == "__main__":
    main()
