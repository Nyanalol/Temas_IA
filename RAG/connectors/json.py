"""
connectors/json.py — Carga ficheros .json y los parte en chunks.

Soporta dos formatos habituales:
  - Array de objetos: [{...}, {...}, ...]
  - Objeto único:     {"clave": "valor", ...}

Cada elemento del array (o el objeto entero) se convierte en un Document.
No requiere dependencias extra: usa el módulo json estándar de Python.
"""

import json
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pathlib import Path


def load_chunks_json():
    """
    Lee todos los .json de inputs/json/ y los parte en chunks.
    """
    BASE_DIR  = Path(__file__).resolve().parent.parent
    data_path = BASE_DIR / "inputs" / "json"

    docs = []

    print("\n[json] Buscando archivos JSON...")
    for file in data_path.glob("*.json"):
        print(f"[json] Leyendo: {file.name}")

        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Normalizamos a lista para manejar los dos formatos
        items = data if isinstance(data, list) else [data]

        for i, item in enumerate(items):
            # Convertimos el objeto a texto plano key: value\n ...
            content = "\n".join(f"{k}: {v}" for k, v in item.items()) if isinstance(item, dict) else str(item)

            docs.append(
                Document(
                    page_content=content,
                    metadata={
                        "source":    file.name,
                        "file_name": file.name,
                        "type":      "json",
                        "index":     i,
                    },
                )
            )

    print(f"[json] Documentos cargados: {len(docs)}")

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks   = splitter.split_documents(docs)
    print(f"[json] Chunks generados: {len(chunks)}")

    return chunks
