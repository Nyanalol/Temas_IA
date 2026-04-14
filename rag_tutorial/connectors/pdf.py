from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pathlib import Path



def load_chunks_pdf():
    BASE_DIR = Path(__file__).resolve().parent.parent
    data_path = BASE_DIR / "inputs" / "pdf"

    docs = []

    print("\n[PDF] Buscando archivos PDF...\n")

    for file in data_path.glob("*.pdf"):
        print(f"Leyendo: {file.name}")

        loader = PyPDFLoader(str(file))
        pdf_docs = loader.load()

        docs.extend(pdf_docs)

    for doc in pdf_docs:
        doc.metadata["type"] = "pdf"
        doc.metadata["file_name"] = file.name

    print(f"\n✔ Total páginas cargadas: {len(docs)}")

    # =========================
    # CHUNKING
    # =========================
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )

    chunks = splitter.split_documents(docs)

    print(f"✔ Total chunks generados: {len(chunks)}\n")


    return chunks