# Temas IA

Proyecto personal de aprendizaje de Inteligencia Artificial con Python y LangChain.

Parte de cero —qué es un embedding, qué es un token— y avanza hacia pipelines RAG completos y agentes con tipos de mensaje. Usa **Ollama** para ejecutar LLMs en local de forma gratuita, con soporte para OpenAI, Anthropic y Groq cuando se quieran probar modelos externos.

---

## Estructura del proyecto

```
Temas_IA/
├── .env.example          # Template de variables de entorno
├── .gitignore
├── pyproject.toml        # Dependencias unificadas de todo el proyecto
├── uv.lock               # Versiones exactas (garantiza reproducibilidad)
│
├── config.py             # Fábrica central de LLM y embeddings (lee .env)
│                         # Cambiar de proveedor = editar .env, sin tocar código
│
├── embeddings/
│   └── embeddings.py     # Experimento 1: tokenización y vectores de frase
│                         # Modelos: DeBERTa (embedding por token)
│                         #          all-mpnet-base-v2 (embedding de frase)
│
├── rag/
│   ├── pipeline.py       # Script principal: carga documentos → indexa → responde
│   ├── local_persist.py  # Gestión del vectorstore ChromaDB en disco
│   ├── override_metadata.py
│   │
│   ├── connectors/       # Loaders de documentos, uno por formato
│   │   ├── _base.py      # Configuración compartida (splitter, rutas de input)
│   │   ├── __init__.py   # Expone load_all() — agrega todos los conectores
│   │   ├── txt.py
│   │   ├── pdf.py
│   │   ├── csv.py
│   │   ├── json.py
│   │   ├── markdown.py
│   │   └── docx.py
│   │
│   └── inputs/           # Pon aquí los documentos que quieres indexar
│       ├── txt/
│       ├── pdf/
│       ├── csv/
│       ├── json/
│       ├── markdown/
│       └── docx/
│
└── agents/
    └── basics.py         # Experimento 2: tipos de mensaje con LangChain
                          # SystemMessage, HumanMessage, AIMessage
```

---

## Poner en marcha en un PC nuevo

### 1. Clonar y situarse en la rama

```bash
git clone https://github.com/Nyanalol/Temas_IA.git
cd Temas_IA
git checkout restructure
```

### 2. Crear el entorno e instalar dependencias

```bash
python -m venv .venv

# Windows
.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate

pip install uv
uv sync          # instala las versiones exactas del uv.lock
```

### 3. Configurar las variables de entorno

```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

Edita `.env` con tu editor. Con la configuración por defecto (`LLM_PROVIDER=ollama`) no necesitas ninguna API key.

### 4. (Solo RAG y Agents) Asegúrate de tener Ollama corriendo

```bash
# Instalar Ollama: https://ollama.com
ollama serve

# Descargar los modelos que usa el proyecto
ollama pull llama3
ollama pull nomic-embed-text
```

### 5. Ejecutar los scripts

| Script | Qué hace |
|---|---|
| `python embeddings/embeddings.py` | Tokenización y vectores de frase con HuggingFace |
| `python rag/pipeline.py` | Pipeline RAG completo: carga docs → indexa → responde |
| `python agents/basics.py` | Intro a tipos de mensaje: System, Human, AI |

---

## Variables de entorno

Ver [.env.example](.env.example) para la lista completa. Las más importantes:

| Variable | Default | Descripción |
|---|---|---|
| `LLM_PROVIDER` | `ollama` | Proveedor LLM activo |
| `LLM_MODEL` | `llama3` | Modelo concreto del proveedor |
| `LLM_TEMPERATURE` | `0` | 0 = determinista, 1 = más creativo |
| `EMBEDDING_PROVIDER` | `ollama` | Proveedor de embeddings |
| `EMBEDDING_MODEL` | `nomic-embed-text` | Modelo de embeddings |

Para cambiar de proveedor, basta con editar estas variables — sin modificar código.

## Proveedores soportados

| Proveedor | Tipo | Key necesaria |
|---|---|---|
| `ollama` | Local, gratuito | — |
| `openai` | API | `OPENAI_API_KEY` |
| `anthropic` | API | `ANTHROPIC_API_KEY` |
| `groq` | API (gratuita con límites) | `GROQ_API_KEY` |

---

## Añadir documentos al RAG

Copia los ficheros en la carpeta correspondiente de `rag/inputs/` y ejecuta `pipeline.py` con `FORCE_REBUILD = True`. El pipeline los indexará automáticamente.

## Añadir un nuevo formato de documento

1. Crea `rag/connectors/{formato}.py` con una función `load() -> list`
2. Importa y llama a `load()` en `rag/connectors/__init__.py` dentro de `load_all()`
3. Crea la carpeta `rag/inputs/{formato}/`
