"""
connectors/markdown.py — Carga ficheros .md y los parte en chunks semánticos.

Usa MarkdownHeaderTextSplitter para dividir primero por secciones (# ## ###),
luego get_splitter() para trocear secciones que sigan siendo demasiado largas.
Así cada chunk corresponde a una unidad lógica del documento.
"""

from langchain_text_splitters import MarkdownHeaderTextSplitter

from ._base import get_splitter, inputs_dir

# Cabeceras usadas como puntos de corte. El valor es el nombre del metadato
# que se añade al chunk para saber a qué sección pertenece.
HEADERS_TO_SPLIT = [("#", "h1"), ("##", "h2"), ("###", "h3")]


def load() -> list:
    """Lee todos los .md de inputs/markdown/ y los parte en chunks por sección."""
    data_path  = inputs_dir("markdown")
    md_split   = MarkdownHeaderTextSplitter(headers_to_split_on=HEADERS_TO_SPLIT, strip_headers=False)
    char_split = get_splitter()
    docs       = []

    print("\n[markdown] Buscando archivos Markdown...")
    for file in data_path.glob("*.md"):
        print(f"[markdown] Leyendo: {file.name}")

        with open(file, "r", encoding="utf-8") as f:
            text = f.read()

        # Primera pasada: divide por cabeceras.
        header_chunks = md_split.split_text(text)
        # Segunda pasada: trocea secciones que superen el chunk_size.
        split_chunks  = char_split.split_documents(header_chunks)

        for chunk in split_chunks:
            chunk.metadata.update({"source": file.name, "file_name": file.name, "type": "markdown"})

        docs.extend(split_chunks)

    print(f"[markdown] Chunks generados: {len(docs)}")
    return docs
