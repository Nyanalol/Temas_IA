"""
connectors/csv.py — Carga ficheros .csv y los parte en chunks.

Usa CSVLoader de langchain_community, que trata cada fila como un Document
independiente. Después se aplica el mismo splitter que en el resto de conectores
por si alguna celda es muy larga.
"""

from langchain_community.document_loaders import CSVLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pathlib import Path


def load_chunks_csv():
    """
    Lee todos los .csv de inputs/csv/ y los parte en chunks.

    Cada fila del CSV se convierte en un Document cuyo contenido es
    "columna: valor, columna: valor, ..." (formato que CSVLoader produce).
    """
    BASE_DIR  = Path(__file__).resolve().parent.parent
    data_path = BASE_DIR / "inputs" / "csv"

    docs = []

    print("\n[csv] Buscando archivos CSV...")
    for file in data_path.glob("*.csv"):
        print(f"[csv] Leyendo: {file.name}")

        # source_column indica qué columna usar como metadato "source".
        # Si no existe esa columna en tu CSV, elimina el argumento.
        loader = CSVLoader(
            file_path=str(file),
            metadata_columns=["source"] if False else [],  # ajusta si quieres
        )
        file_docs = loader.load()

        # Añadimos metadatos comunes
        for doc in file_docs:
            doc.metadata["type"]      = "csv"
            doc.metadata["file_name"] = file.name

        docs.extend(file_docs)

    print(f"[csv] Documentos cargados: {len(docs)}")

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks   = splitter.split_documents(docs)
    print(f"[csv] Chunks generados: {len(chunks)}")

    return chunks
