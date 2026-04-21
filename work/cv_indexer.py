"""
cv_indexer.py — Indexa los CVs en PDF en un vectorstore ChromaDB dedicado.

Uso:
    from work.cv_indexer import build_cv_vectorstore, get_cv_retriever

Los PDFs deben estar en work/inputs/cv/. Se detecta el idioma
automáticamente por el nombre del archivo (p. ej. cv_es.pdf, cv_en.pdf).
"""

from pathlib import Path

from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import get_embeddings

CV_INPUTS_PATH = Path(__file__).resolve().parent / "inputs" / "cv"
CHROMA_PATH = Path(__file__).resolve().parent / "chroma_db"

CHUNK_SIZE = 600
CHUNK_OVERLAP = 80


def _detect_language(filename: str) -> str:
    name = filename.lower()
    if any(k in name for k in ("_en", "_eng", "english", "ingles", "inglés")):
        return "en"
    if any(k in name for k in ("_es", "_esp", "spanish", "español", "castellano")):
        return "es"
    return "unknown"


def _load_cv_chunks() -> list:
    pdf_files = list(CV_INPUTS_PATH.glob("*.pdf"))
    if not pdf_files:
        raise FileNotFoundError(
            f"No se encontraron PDFs en {CV_INPUTS_PATH}. "
            "Copia tus CVs (cv_es.pdf, cv_en.pdf, ...) en work/inputs/cv/ antes de continuar."
        )

    docs = []
    for pdf_file in pdf_files:
        print(f"[cv_indexer] Leyendo: {pdf_file.name}")
        pages = PyPDFLoader(str(pdf_file)).load()
        lang = _detect_language(pdf_file.name)
        for page in pages:
            page.metadata["source_file"] = pdf_file.name
            page.metadata["type"] = "cv"
            page.metadata["language"] = lang
        docs.extend(pages)

    splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    chunks = splitter.split_documents(docs)
    print(f"[cv_indexer] Chunks generados: {len(chunks)}")
    return chunks


def build_cv_vectorstore(force_rebuild: bool = False) -> Chroma:
    """Carga o crea el vectorstore con los CVs. Devuelve la instancia de Chroma."""
    embedding_model = get_embeddings()
    path_str = str(CHROMA_PATH)

    if not force_rebuild and CHROMA_PATH.exists() and any(CHROMA_PATH.iterdir()):
        print("[cv_indexer] Cargando vectorstore desde disco...")
        return Chroma(persist_directory=path_str, embedding_function=embedding_model)

    print("[cv_indexer] Creando vectorstore nuevo...")
    chunks = _load_cv_chunks()
    vs = Chroma.from_documents(
        documents=chunks,
        embedding=embedding_model,
        persist_directory=path_str,
    )
    print("[cv_indexer] Vectorstore creado y persistido.")
    return vs


def get_cv_retriever(k: int = 6, force_rebuild: bool = False):
    """Devuelve un retriever listo para usar en cadenas LCEL."""
    vs = build_cv_vectorstore(force_rebuild=force_rebuild)
    return vs.as_retriever(search_kwargs={"k": k})
