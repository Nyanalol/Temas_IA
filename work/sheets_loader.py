"""
sheets_loader.py — Lee una Google Sheet pública exportada como CSV.

La sheet debe ser pública (Anyone with the link can view).
Se acepta tanto la URL normal de Google Sheets como la URL de exportación directa.

Ejemplo de URL normal:
    https://docs.google.com/spreadsheets/d/ABC123/edit#gid=0

Se convierte automáticamente a:
    https://docs.google.com/spreadsheets/d/ABC123/export?format=csv&gid=0
"""

import csv
import io
import re
import urllib.request


def _to_csv_export_url(url: str) -> str:
    """Convierte una URL normal de Google Sheets a URL de exportación CSV."""
    if "export?format=csv" in url:
        return url

    match = re.search(r"/spreadsheets/d/([a-zA-Z0-9_-]+)", url)
    if not match:
        raise ValueError(
            f"URL de Google Sheets no reconocida: {url}\n"
            "Asegúrate de que sea una URL de Google Sheets válida."
        )
    sheet_id = match.group(1)
    gid_match = re.search(r"[?&#]gid=(\d+)", url)
    gid = gid_match.group(1) if gid_match else "0"
    return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"


def load_sheet_as_text(url: str) -> str:
    """
    Descarga una Google Sheet pública y devuelve su contenido como
    texto con formato tabla legible para el LLM.

    Devuelve una cadena con cabeceras y filas separadas por ' | '.
    """
    csv_url = _to_csv_export_url(url)
    print(f"[sheets_loader] Descargando: {csv_url}")

    req = urllib.request.Request(csv_url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:  # noqa: S310
        content = resp.read().decode("utf-8")

    reader = csv.DictReader(io.StringIO(content))
    rows = list(reader)

    if not rows:
        return "(La hoja de cálculo está vacía)"

    headers = list(rows[0].keys())
    lines = [" | ".join(headers)]
    lines.append("-" * max(len(lines[0]), 40))
    for row in rows:
        line = " | ".join(str(row.get(h, "")).strip() for h in headers)
        if line.strip(" |"):  # skip fully empty rows
            lines.append(line)

    return "\n".join(lines)
