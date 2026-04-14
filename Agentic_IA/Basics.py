from dotenv import load_dotenv
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_community.vectorstores import Chroma

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

query = "Dame el ejemplo de registro de log en mis documentos"
model = "llama3"
temperature = 0

# LLM
llm = ChatOllama(model=model, temperature=temperature)