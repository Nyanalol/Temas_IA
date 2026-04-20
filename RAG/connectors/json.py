"""
connectors/json.py — Carga ficheros .json y los parte en chunks.

Soporta dos formatos:
  - Array de objetos : [{...}, {...}, ...]
  - Objeto único     : {"clave": "valor", ...}

No requiere dependencias extra: usa el módulo json de la stdlib.
"""

import json

from langchain_core.documents import Document

from ._base import get_splitter, inputs_dir


def load() -> list:
    """Lee todos los .json de inputs/json/ y los parte en chunks."""
    data_path = inputs_dir("json")
    docs      = []

    print("\n[json] Buscando archivos JSON...")
    for file in data_path.glob("*.json"):
        print(f"[json] Leyendo: {file.name}")

        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Normalizamos a lista para manejar los dos formatos
        items = data if isinstance(data, list) else [data]

        for i, item in enumerate(items):
            content = (
                "\n".join(f"{k}: {v}" for k, v in item.items())
                if isinstance(item, dict)
                else str(item)
            )
            docs.append(
                Document(
                    page_content=content,
                    metadata={"source": file.name, "file_name": file.name, "type": "json", "index": i},
                )
            )

    print(f"[json] Documentos cargados: {len(docs)}")
    chunks = get_splitter().split_documents(docs)
    print(f"[json] Chunks generados: {len(chunks)}")
    return chunks
