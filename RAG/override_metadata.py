"""
override_metadata.py — Sobreescribe los metadatos de una lista de Documents.

Útil cuando quieres etiquetar manualmente un lote de documentos,
por ejemplo para diferenciar fuentes o equipos en el vectorstore.
"""


def override_metadata(chunks, source, developer):
    """
    Sustituye los metadatos de cada chunk por source y developer.

    Parámetros
    ----------
    chunks    : lista de Documents (resultado de un splitter)
    source    : etiqueta de la fuente (p.ej. "Ministerio")
    developer : etiqueta del desarrollador que hizo la carga
    """
    for chunk in chunks:
        chunk.metadata = {"source": source, "developer": developer}

    return chunks