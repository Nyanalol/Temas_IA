"""
connectors/_base.py — Utilidades compartidas por todos los conectores.

Centraliza la configuración del splitter y la resolución de rutas,
evitando repetir los mismos parámetros en cada conector.
"""

from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Tamaño máximo de cada chunk (en caracteres).
CHUNK_SIZE = 500

# Solapamiento entre chunks consecutivos para no perder contexto en los cortes.
CHUNK_OVERLAP = 50


def inputs_dir(fmt: str) -> Path:
    """
    Devuelve la ruta a rag/inputs/{fmt}/.

    Todos los conectores guardan sus ficheros bajo esa carpeta,
    organizados por formato (txt, pdf, csv, json, markdown, docx).
    """
    return Path(__file__).resolve().parent.parent / "inputs" / fmt


def get_splitter() -> RecursiveCharacterTextSplitter:
    """
    Devuelve una instancia del splitter con la configuración estándar.

    RecursiveCharacterTextSplitter intenta dividir por párrafos, luego
    por frases, etc., antes de cortar en medio del texto. Es el splitter
    de propósito general más recomendado para RAG.
    """
    return RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
