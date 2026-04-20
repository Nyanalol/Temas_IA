"""
connectors/csv.py — Carga ficheros .csv y los parte en chunks.

CSVLoader trata cada fila como un Document independiente.
El contenido de cada Document es "columna: valor" por línea.
"""

from langchain_community.document_loaders import CSVLoader

from ._base import get_splitter, inputs_dir


def load() -> list:
    """Lee todos los .csv de inputs/csv/ y los parte en chunks."""
    data_path = inputs_dir("csv")
    docs      = []

    print("\n[csv] Buscando archivos CSV...")
    for file in data_path.glob("*.csv"):
        print(f"[csv] Leyendo: {file.name}")

        file_docs = CSVLoader(file_path=str(file)).load()

        for doc in file_docs:
            doc.metadata["type"]      = "csv"
            doc.metadata["file_name"] = file.name

        docs.extend(file_docs)

    print(f"[csv] Documentos cargados: {len(docs)}")
    chunks = get_splitter().split_documents(docs)
    print(f"[csv] Chunks generados: {len(chunks)}")
    return chunks
