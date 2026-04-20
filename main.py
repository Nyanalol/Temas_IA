"""
Entry point for the incident analysis chain.
"""

import logging
import subprocess
import time
import urllib.request
import urllib.error

from agents.chain_factory import build_incident_chain


def _ensure_ollama_running(timeout: int = 10) -> None:
    url = "http://127.0.0.1:11434"
    try:
        urllib.request.urlopen(url, timeout=2)
        return
    except Exception:
        pass

    logging.getLogger(__name__).info("Ollama no responde, arrancando...")
    subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            urllib.request.urlopen(url, timeout=2)
            logging.getLogger(__name__).info("Ollama listo.")
            return
        except Exception:
            time.sleep(1)

    raise RuntimeError(f"Ollama no arrancó en {timeout}s. Comprueba la instalación.")

logging.basicConfig(
    level=logging.WARNING,
    format="%(name)s | %(levelname)s | %(message)s",
)
logging.getLogger("agents").setLevel(logging.DEBUG)

USER_MESSAGE = (
    "The daily sales pipeline failed at 06:10. "
    "The silver job for customer_orders crashed because the source file "
    "arrived without customer_id. "
    "This is high priority because the finance dashboard was not refreshed."
)


def _section(title: str) -> None:
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def main():
    _ensure_ollama_running()
    chain = build_incident_chain()

    _section("INPUT_ORIGINAL")
    print(USER_MESSAGE)

    result = chain.invoke({"user_message": USER_MESSAGE})

    _section("FINAL_RESULT")
    print(result)

    _section("FINAL_FIELDS")
    print("incident_summary:", result.incident_summary)
    print("business_impact:", result.business_impact)
    print("next_action:", result.next_action)
    print("owner_team:", result.owner_team)


if __name__ == "__main__":
    main()
