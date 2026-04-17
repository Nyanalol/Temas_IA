# WIP — Tools (Herramientas para agentes)

Los LLMs por sí solos solo generan texto. Con **tools** (function calling) el modelo puede decidir cuándo llamar a una función externa — buscar en la web, leer un fichero, llamar a una API — e integrar el resultado en su respuesta.

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

### 5. AgentExecutor
El bucle completo: LLM decide qué herramienta usar → se ejecuta → resultado vuelve al LLM → respuesta final.

---

## Ideas de scripts a crear

- `builtin_tools.py` — usar herramientas predefinidas (búsqueda web, Wikipedia)
- `custom_tool.py` — crear una tool personalizada con `@tool`
- `agent_with_tools.py` — agente completo con varias herramientas
- `rag_as_tool.py` — el pipeline RAG como herramienta de un agente

---

## Recursos
- [LangChain Tools](https://python.langchain.com/docs/concepts/tools/)
- [LangChain Agents](https://python.langchain.com/docs/concepts/agents/)
