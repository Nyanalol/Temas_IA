"""
connectors/__init__.py — Punto de entrada del paquete de conectores.

Expone load_all() para cargar documentos de todos los formatos soportados
con una sola llamada desde el pipeline principal.

Para añadir un nuevo formato:
  1. Crea connectors/{formato}.py con una función load() -> list
  2. Añade la importación y la llamada en load_all()
"""

from .csv import load as load_csv
from .docx import load as load_docx
from .json import load as load_json
from .markdown import load as load_markdown
from .pdf import load as load_pdf
from .txt import load as load_txt


def load_all() -> list:
    """
    Carga y parte en chunks todos los documentos de inputs/,
    sin importar el formato.

    Devuelve una lista plana de Documents lista para ser indexada
    en el vectorstore.
    """
    return (
        load_txt()
        + load_pdf()
        + load_csv()
        + load_json()
        + load_markdown()
        + load_docx()
    )
