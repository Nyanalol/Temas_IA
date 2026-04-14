from dotenv import load_dotenv
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from connectors.txt import load_chunks
from connectors.pdf import load_chunks_pdf
from override_metadata import override_metadata
from local_persist import persist_vectorstore
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
persist_path = BASE_DIR / "chroma_db"

override = True
force_rebuild = True
source = "Ministerio"
developer = "MA"
query = "Dame el ejemplo de registro de log en mis documentos"

load_dotenv()

# LLM
llm = ChatOllama(model="llama3", temperature=0)

# Embeddings
embedding_model = OllamaEmbeddings(model="nomic-embed-text")

# Cargar datos

txt_chunks = load_chunks()
pdf_chunks = load_chunks_pdf()

chunks = txt_chunks + pdf_chunks

print(f"Chunks TXT: {len(txt_chunks)}")
print(f"Chunks PDF: {len(pdf_chunks)}")
print(f"Chunks totales: {len(chunks)}")

if override:
    chunks = override_metadata(chunks, source, developer)

vectorstore = persist_vectorstore(chunks, embedding_model, persist_path, force_rebuild)

print("Vectorstore listo")

# Query

relevant_docs = vectorstore.similarity_search(query, k=5)

# Respuesta
context = "\n\n".join(doc.page_content for doc in relevant_docs)

prompt = f"""
Contexto:
{context}

Pregunta:
{query}
"""

response = llm.invoke(prompt)

print(query)
print("\nRespuesta:")
print(response.content)