"""
rag.py — Pipeline principal de RAG (Retrieval-Augmented Generation).

Flujo:
  1. Cargar documentos (txt + pdf) desde inputs/
  2. Partir en chunks
  3. Generar embeddings e indexar en ChromaDB
  4. Buscar chunks relevantes para la query
  5. Construir un prompt con ese contexto y preguntar al LLM

Ejecución (desde la raíz del proyecto):
    python rag/rag.py
"""

import sys
from pathlib import Path

# Añadimos la raíz al path para poder importar config.py.
# Añadimos rag/ para poder importar connectors, local_persist, etc.
ROOT = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))

from config import get_llm, get_embeddings
from connectors.txt import load_chunks
from connectors.pdf import load_chunks_pdf
from connectors.csv import load_chunks_csv
from connectors.json import load_chunks_json
from connectors.markdown import load_chunks_markdown
from connectors.docx import load_chunks_docx
from override_metadata import override_metadata
from local_persist import persist_vectorstore


# ── Configuración del script ───────────────────────────────────────────────────

PERSIST_PATH  = HERE / "chroma_db"

# Si override=True, sobreescribe los metadatos de todos los documentos
# con source y developer. Útil para etiquetar cargas de prueba.
OVERRIDE      = True
SOURCE        = "Ministerio"
DEVELOPER     = "MA"

# force_rebuild=True borra y recrea el vectorstore aunque ya exista.
# Ponlo a False cuando no hayas cambiado los documentos, para ir más rápido.
FORCE_REBUILD = True

QUERY = "Dame el ejemplo de registro de log en mis documentos"


# ── Pipeline ───────────────────────────────────────────────────────────────────

def main():
    # LLM y embeddings se crean desde config.py (que lee el .env).
    llm             = get_llm()
    embedding_model = get_embeddings()

    # ── Carga de documentos ───────────────────────────────────────────────────
    print("\n[RAG] Cargando documentos...")
    txt_chunks      = load_chunks()
    pdf_chunks      = load_chunks_pdf()
    csv_chunks      = load_chunks_csv()
    json_chunks     = load_chunks_json()
    markdown_chunks = load_chunks_markdown()
    docx_chunks     = load_chunks_docx()

    chunks = txt_chunks + pdf_chunks + csv_chunks + json_chunks + markdown_chunks + docx_chunks
    print(f"[RAG] Total chunks generados: {len(chunks)}")

    # ── Metadatos opcionales ──────────────────────────────────────────────────
    if OVERRIDE:
        chunks = override_metadata(chunks, SOURCE, DEVELOPER)
        print(f"[RAG] Metadatos sobreescritos → source={SOURCE}, developer={DEVELOPER}")

    # ── Vectorstore ───────────────────────────────────────────────────────────
    vectorstore = persist_vectorstore(chunks, embedding_model, PERSIST_PATH, FORCE_REBUILD)
    if vectorstore is None:
        print("[RAG] Error: no se pudo inicializar el vectorstore. Abortando.")
        return

    # ── Búsqueda por similitud ────────────────────────────────────────────────
    print(f"\n[RAG] Query: {QUERY}")
    relevant_docs = vectorstore.similarity_search(QUERY, k=5)
    print(f"[RAG] Documentos recuperados: {len(relevant_docs)}")

    # ── Construcción del prompt ───────────────────────────────────────────────
    # El contexto es la concatenación del contenido de los chunks recuperados.
    context = "\n\n".join(doc.page_content for doc in relevant_docs)

    prompt = f"""Contexto:
{context}

Pregunta:
{QUERY}"""

    # ── Respuesta del LLM ─────────────────────────────────────────────────────
    response = llm.invoke(prompt)

    print("\n[RAG] Respuesta:")
    print(response.content)


if __name__ == "__main__":
    main()