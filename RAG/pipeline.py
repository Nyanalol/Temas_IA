"""
pipeline.py — Pipeline principal de RAG (Retrieval-Augmented Generation).

Flujo:
  1. Cargar documentos de todos los formatos en inputs/
  2. Generar embeddings e indexar en ChromaDB
  3. Buscar chunks relevantes para la query
  4. Construir un prompt con ese contexto y preguntar al LLM

Ejecución (desde la raíz del proyecto):
    python -m rag.pipeline
"""

from pathlib import Path

from config import get_llm, get_embeddings
from rag.connectors import load_all
from rag.override_metadata import override_metadata
from rag.local_persist import persist_vectorstore


# ── Configuración ──────────────────────────────────────────────────────────────

PERSIST_PATH = Path(__file__).resolve().parent / "chroma_db"

# Si OVERRIDE=True, sobreescribe los metadatos de todos los documentos
# con SOURCE y DEVELOPER. Útil para etiquetar cargas de prueba.
OVERRIDE  = True
SOURCE    = "Ministerio"
DEVELOPER = "MA"

# Si FORCE_REBUILD=True, recrea el vectorstore aunque ya exista en disco.
# Ponlo a False cuando no hayas cambiado los documentos, para ir más rápido.
FORCE_REBUILD = True

QUERY = "Dame el ejemplo de registro de log en mis documentos"


# ── Pipeline ───────────────────────────────────────────────────────────────────

def main():
    llm             = get_llm()
    embedding_model = get_embeddings()

    # ── Carga de documentos ───────────────────────────────────────────────────
    # load_all() llama a todos los conectores y devuelve una lista plana.
    print("\n[RAG] Cargando documentos...")
    chunks = load_all()
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

    # ── Prompt y respuesta ────────────────────────────────────────────────────
    # El contexto son los chunks recuperados, concatenados con separadores.
    context  = "\n\n".join(doc.page_content for doc in relevant_docs)
    prompt   = f"Contexto:\n{context}\n\nPregunta:\n{QUERY}"
    response = llm.invoke(prompt)

    print("\n[RAG] Respuesta:")
    print(response.content)


if __name__ == "__main__":
    main()
