"""
connectors/pdf.py — Carga ficheros .pdf y los parte en chunks.
"""

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pathlib import Path


def load_chunks_pdf():
    """
    Lee todos los .pdf de inputs/pdf/, los convierte en Documents
    (una página = un Document) y los parte en chunks con solapamiento.
    """
    BASE_DIR  = Path(__file__).resolve().parent.parent
    data_path = BASE_DIR / "inputs" / "pdf"

    docs = []

    print("\n[pdf] Buscando archivos PDF...")

    for file in data_path.glob("*.pdf"):
        print(f"[pdf] Leyendo: {file.name}")

        loader   = PyPDFLoader(str(file))
        pdf_docs = loader.load()

        # Añadimos metadatos a las páginas de este fichero antes de agregarlo.
        for doc in pdf_docs:
            doc.metadata["type"]      = "pdf"
            doc.metadata["file_name"] = file.name

        docs.extend(pdf_docs)

    print(f"[pdf] Total páginas cargadas: {len(docs)}")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
    )

    chunks = splitter.split_documents(docs)
    print(f"[pdf] Chunks generados: {len(chunks)}")

    return chunks