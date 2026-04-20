"""
local_persist.py — Gestión del vectorstore ChromaDB en disco.

Permite reutilizar un índice ya generado (force_rebuild=False) o
recrearlo desde cero (force_rebuild=True). Así evitas re-embeddear
todos los documentos cada vez que ejecutas el script.
"""

from langchain_chroma import Chroma


def persist_vectorstore(chunks, embedding_model, persist_path, force_rebuild):
    """
    Carga o crea un vectorstore ChromaDB persistido en disco.

    Parámetros
    ----------
    chunks         : lista de Documents ya procesados
    embedding_model: instancia del modelo de embeddings
    persist_path   : Path donde guardar/leer el índice
    force_rebuild  : si True, recrea el índice aunque ya exista
    """
    persist_path_str = str(persist_path)

    try:
        if not force_rebuild and persist_path.exists() and any(persist_path.iterdir()):
            print("[persist] Cargando vectorstore desde disco...")
            vectorstore = Chroma(
                persist_directory=persist_path_str,
                embedding_function=embedding_model,
            )
            print("[persist] Vectorstore cargado correctamente")
        else:
            print("[persist] Creando vectorstore nuevo...")
            vectorstore = Chroma.from_documents(
                documents=chunks,
                embedding=embedding_model,
                persist_directory=persist_path_str,
            )
            print("[persist] Vectorstore creado y persistido correctamente")

        return vectorstore

    except Exception as e:
        print(f"[persist] Error con el vectorstore: {e}")
        return None
