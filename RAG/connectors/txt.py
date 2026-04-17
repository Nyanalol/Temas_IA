"""
connectors/txt.py — Carga ficheros .txt y los parte en chunks.
"""

from langchain_core.documents import Document
from ._base import inputs_dir, get_splitter


def load() -> list:
    """Lee todos los .txt de inputs/txt/ y los parte en chunks."""
    data_path = inputs_dir("txt")
    docs      = []

    print("\n[txt] Buscando archivos .txt...")
    for file in data_path.glob("*.txt"):
        print(f"[txt] Leyendo: {file.name}")
        with open(file, "r", encoding="utf-8") as f:
            text = f.read()

        docs.append(
            Document(
                page_content=text,
                metadata={"source": file.name, "path": str(file), "type": "txt"},
            )
        )

    print(f"[txt] Documentos cargados: {len(docs)}")
    chunks = get_splitter().split_documents(docs)
    print(f"[txt] Chunks generados: {len(chunks)}")
    return chunks