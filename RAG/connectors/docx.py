"""
connectors/docx.py — Carga ficheros .docx (Word) y los parte en chunks.

Usa Docx2txtLoader para extraer el texto plano del documento.
Requiere el paquete 'docx2txt' (incluido en pyproject.toml).
"""

from langchain_community.document_loaders import Docx2txtLoader
from ._base import inputs_dir, get_splitter


def load() -> list:
    """Lee todos los .docx de inputs/docx/ y los parte en chunks."""
    data_path = inputs_dir("docx")
    docs      = []

    print("\n[docx] Buscando archivos Word (.docx)...")
    for file in data_path.glob("*.docx"):
        print(f"[docx] Leyendo: {file.name}")

        file_docs = Docx2txtLoader(str(file)).load()

        for doc in file_docs:
            doc.metadata["type"]      = "docx"
            doc.metadata["file_name"] = file.name

        docs.extend(file_docs)

    print(f"[docx] Documentos cargados: {len(docs)}")
    chunks = get_splitter().split_documents(docs)
    print(f"[docx] Chunks generados: {len(chunks)}")
    return chunks
