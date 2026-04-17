"""
connectors/markdown.py — Carga ficheros .md y los parte en chunks semánticos.

En lugar del splitter de caracteres genérico, usamos MarkdownHeaderTextSplitter,
que divide el documento siguiendo la jerarquía de cabeceras (# ## ###).
Así cada chunk corresponde a una sección lógica del documento.
"""

from langchain_core.documents import Document
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from pathlib import Path


# Cabeceras que usamos como puntos de corte, de mayor a menor rango.
# Valor: nombre del metadato que se añade al chunk.
HEADERS_TO_SPLIT = [
    ("#",   "h1"),
    ("##",  "h2"),
    ("###", "h3"),
]


def load_chunks_markdown():
    """
    Lee todos los .md de inputs/markdown/ y los parte en chunks por sección.
    """
    BASE_DIR  = Path(__file__).resolve().parent.parent
    data_path = BASE_DIR / "inputs" / "markdown"

    docs = []

    print("\n[markdown] Buscando archivos Markdown...")
    for file in data_path.glob("*.md"):
        print(f"[markdown] Leyendo: {file.name}")

        with open(file, "r", encoding="utf-8") as f:
            text = f.read()

        # Primera pasada: divide por cabeceras.
        # Cada chunk lleva en metadata el texto de las cabeceras que lo contienen.
        md_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=HEADERS_TO_SPLIT,
            strip_headers=False,  # conserva el texto del header dentro del chunk
        )
        header_chunks = md_splitter.split_text(text)

        # Segunda pasada: si alguna sección es muy larga, la cortamos también.
        char_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        split_chunks  = char_splitter.split_documents(header_chunks)

        # Añadimos metadatos de fichero
        for chunk in split_chunks:
            chunk.metadata["source"]    = file.name
            chunk.metadata["file_name"] = file.name
            chunk.metadata["type"]      = "markdown"

        docs.extend(split_chunks)

    print(f"[markdown] Chunks generados: {len(docs)}")
    return docs
