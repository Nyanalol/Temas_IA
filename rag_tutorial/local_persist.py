from langchain_chroma import Chroma


def persist_vectorstore(chunks, embedding_model, persist_path, force_rebuild):
    persist_path_str = str(persist_path)

    try:
        if force_rebuild==False and persist_path.exists() and any(persist_path.iterdir()):
            print("Cargando vectorstore ya persistido...")
            vectorstore = Chroma(
                persist_directory=persist_path_str,
                embedding_function=embedding_model
            )
            print("Vectorstore cargado desde disco")
        else:
            print("No existe vectorstore persistido, creando uno nuevo...")
            vectorstore = Chroma.from_documents(
                documents=chunks,
                embedding=embedding_model,
                persist_directory=persist_path_str
            )
            print("Vectorstore creado y persistido correctamente")
            
        return vectorstore
    except Exception as e:
        print("Error con el vectorstore:")
        print(e)
        return None