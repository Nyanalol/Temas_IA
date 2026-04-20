"""
connectors/pdf.py — Carga ficheros .pdf y los parte en chunks.

PyPDFLoader convierte cada página en un Document independiente,
manteniendo los metadatos de página y origen que añade LangChain.
"""

from langchain_community.document_loaders import PyPDFLoader

from ._base import get_splitter, inputs_dir


def load() -> list:
    """Lee todos los .pdf de inputs/pdf/ y los parte en chunks."""
    data_path = inputs_dir("pdf")
    docs      = []

    print("\n[pdf] Buscando archivos PDF...")
    for file in data_path.glob("*.pdf"):
        print(f"[pdf] Leyendo: {file.name}")

        pdf_docs = PyPDFLoader(str(file)).load()

        for doc in pdf_docs:
            doc.metadata["type"]      = "pdf"
            doc.metadata["file_name"] = file.name

        docs.extend(pdf_docs)

    print(f"[pdf] Páginas cargadas: {len(docs)}")
    chunks = get_splitter().split_documents(docs)
    print(f"[pdf] Chunks generados: {len(chunks)}")
    return chunks
