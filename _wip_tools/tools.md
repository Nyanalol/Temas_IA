# WIP — Tools (Herramientas para agentes)

Los LLMs por sí solos solo generan texto. Con **tools** (function calling) el modelo puede decidir cuándo llamar a una función externa — buscar en la web, leer un fichero, llamar a una API — e integrar el resultado en su respuesta.

> **Cubierto en el curso de LangChain:**
> - `3:55:21` ReAct Agent Framework
> - `4:12:26` ReAct Agent In Langchain With Streams
> - `4:42:12` SQL ReAct Agent
>
> **Cubierto en el curso de LangGraph:**
> - `2:55:51` Tool Binding
> - `3:30:10` Build ReAct Agent With LangGraph
>
> Los scripts de esta carpeta amplían esos conceptos con herramientas propias.

---

## Qué aprenderás aquí

### 1. Qué es function calling
El LLM recibe una lista de herramientas disponibles (con su nombre, descripción y parámetros). Cuando lo necesita, devuelve una llamada estructurada a esa función en vez de texto libre. Tu código ejecuta la función y le devuelve el resultado al modelo.

### 2. Tools predefinidas de LangChain
LangChain incluye herramientas listas para usar:
- `DuckDuckGoSearchRun` — búsqueda web
- `WikipediaQueryRun` — consultar Wikipedia
- `PythonREPLTool` — ejecutar código Python
- `FileSystemTool` — leer/escribir ficheros

### 3. Crear tools personalizadas
Con el decorador `@tool` conviertes cualquier función Python en una herramienta:
```python
from langchain_core.tools import tool

@tool
def get_weather(city: str) -> str:
    """Devuelve el tiempo actual en una ciudad."""
    # lógica aquí
    return f"En {city} hay 22°C y sol."
```

### 4. Bind tools al LLM
```python
llm_with_tools = llm.bind_tools([get_weather, ...])
```

### 5. SQL Agent
Un agente especializado que puede ejecutar consultas SQL sobre una base de datos. El LLM genera la query, la ejecuta, ve el resultado, y responde. Ver timestamp `4:42:12` del curso de LangChain.

### 6. Tool Binding en LangGraph
En LangGraph las herramientas se integran como nodos del grafo, con más control sobre cuándo y cómo se ejecutan. Ver `_wip_langgraph/`.

---

## Ideas de scripts a crear

- `builtin_tools.py` — usar herramientas predefinidas (búsqueda web, Wikipedia)
- `custom_tool.py` — crear una tool personalizada con `@tool`
- `agent_with_tools.py` — agente completo con varias herramientas
- `sql_agent.py` — agente con acceso a base de datos SQL
- `rag_as_tool.py` — el pipeline RAG como herramienta de un agente

---

## Recursos
- [LangChain Tools](https://python.langchain.com/docs/concepts/tools/)
- [LangChain Agents](https://python.langchain.com/docs/concepts/agents/)
