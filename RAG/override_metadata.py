def override_metadata(chunks, source, developer):
    for i in chunks:
        i.metadata = {"source": source,
                      "developer": developer}

    return chunks