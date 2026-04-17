"""
connectors/docx.py — Carga ficheros .docx (Word) y los parte en chunks.

Usa Docx2txtLoader de langchain_community, que extrae el texto plano
del documento. Requiere el paquete 'docx2txt' (incluido en pyproject.toml).
"""

from langchain_community.document_loaders import Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pathlib import Path


def load_chunks_docx():
    """
    Lee todos los .docx de inputs/docx/ y los parte en chunks.
    """
    BASE_DIR  = Path(__file__).resolve().parent.parent
    data_path = BASE_DIR / "inputs" / "docx"

    docs = []

    print("\n[docx] Buscando archivos Word (.docx)...")
    for file in data_path.glob("*.docx"):
        print(f"[docx] Leyendo: {file.name}")

        loader   = Docx2txtLoader(str(file))
        file_docs = loader.load()

        for doc in file_docs:
            doc.metadata["type"]      = "docx"
            doc.metadata["file_name"] = file.name

        docs.extend(file_docs)

    print(f"[docx] Documentos cargados: {len(docs)}")

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks   = splitter.split_documents(docs)
    print(f"[docx] Chunks generados: {len(chunks)}")

    return chunks
