"""
connectors/txt.py — Carga ficheros .txt y los parte en chunks.
"""

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pathlib import Path


def load_chunks():
    """
    Lee todos los .txt de inputs/txt/, los convierte en Documents
    y los parte en chunks con solapamiento.
    """
    BASE_DIR  = Path(__file__).resolve().parent.parent
    data_path = BASE_DIR / "inputs" / "txt"

    docs = []

    print("\n[txt] Buscando archivos .txt...")
    for file in data_path.glob("*.txt"):
        print(f"[txt] Leyendo: {file.name}")
        with open(file, "r", encoding="utf-8") as f:
            text = f.read()

        docs.append(
            Document(
                page_content=text,
                metadata={
                    "source": file.name,
                    "path": str(file),
                    "type": "txt",
                },
            )
        )

    print(f"[txt] Documentos cargados: {len(docs)}")

    # chunk_size=500  → máximo de caracteres por chunk
    # chunk_overlap=50 → los chunks se solapan 50 caracteres para no perder contexto en los cortes
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
    )

    chunks = splitter.split_documents(docs)
    print(f"[txt] Chunks generados: {len(chunks)}")

    return chunks