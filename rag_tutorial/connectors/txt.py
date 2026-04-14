from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from pathlib import Path


def load_chunks ():
    BASE_DIR = Path(__file__).resolve().parent.parent
    data_path = BASE_DIR / "inputs" / "txt"

    docs = []

    for file in data_path.glob("*.txt"):
        with open(file, "r", encoding="utf-8") as f:
            text = f.read()

            docs.append(
                Document(
                    page_content=text,
                    metadata={
                        "source": file.name,
                        "path": str(file),
                        "type": "txt"
                    }
                )
            )


    #### Chunks
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )

    chunks = splitter.split_documents(docs)

    return chunks