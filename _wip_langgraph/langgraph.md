# WIP — LangGraph

LangGraph es el framework de LangChain para construir agentes y flujos de trabajo complejos como **grafos de estado**. A diferencia del `AgentExecutor` clásico (lineal), LangGraph permite ciclos, bifurcaciones, paralelismo y estado persistente entre pasos.

> Es el siguiente curso después de LangChain. Mucho del contenido (ReAct, herramientas, memoria) se repite desde un enfoque diferente — más control granular.

---

## Temario del curso que seguirás

| Timestamp | Tema | Relación con lo ya visto |
|---|---|---|
| 0:00 – 39:46 | Intro, AI Agent vs Agentic AI, ReAct Architecture | Repaso de `agents/` |
| 39:47 | **LangGraph Setup** | Nuevo |
| 1:04:00 | Connecting to LLMs | Igual que `config.py` |
| 1:20:08 | **First State Graph** | Concepto clave nuevo |
| 1:50:07 | **Pydantic Schemas in Graphs** | Amplía lo de TypedDict del curso de LangChain |
| 2:11:30 | Messages in LangGraph | Similar a `agents/basics.py` pero en grafo |
| 2:42:36 | Prompt Templates | Igual que LangChain |
| 2:55:51 | **Tool Binding** | Amplía `_wip_tools/` |
| 3:30:10 | **Build ReAct Agent with LangGraph** | Versión avanzada de lo de LangChain |
| 4:04:28 | **Parallelization Workflow** | Nuevo |
| 4:18:25 | **Routing Workflow** | Similar a conditional chains |
| 4:38:37 | **Orchestrator-Worker Workflow** | Nuevo — muy útil en agentes complejos |
| 5:17:42 | **Generator-Evaluator Workflow** | Nuevo |
| 5:44:55 | **Manage Memory in LangGraph** | Amplía `_wip_memory/` |
| 5:58:34 | **Human in the Loop** | Nuevo — agentes que piden confirmación |

---

## Conceptos clave nuevos (que no están en el curso de LangChain)

### StateGraph
El grafo tiene un **estado** tipado (un TypedDict o Pydantic model) que fluye entre los nodos. Cada nodo lo puede leer y modificar.

```python
from langgraph.graph import StateGraph, START, END
from typing import TypedDict

class State(TypedDict):
    messages: list
    next_step: str

graph = StateGraph(State)
graph.add_node("llm", call_llm)
graph.add_edge(START, "llm")
graph.add_edge("llm", END)
app = graph.compile()
```

### Conditional Edges (Routing)
Bifurcaciones: según el estado, el flujo va a un nodo u otro. Útil para decidir si llamar a una herramienta o responder directamente.

### Parallelization
Varios nodos se ejecutan en paralelo (broadcasteando el estado) y sus resultados se combinan. Útil para llamar a varias herramientas simultáneamente.

### Orchestrator-Worker
Un nodo orquestador decide qué "workers" (agentes especializados) lanzar. Cada worker es en sí mismo un subgrafo.

### Human in the Loop
El grafo puede pausarse, esperar confirmación humana y continuar. Fundamental para agentes que toman acciones con consecuencias reales.

---

## Ideas de scripts a crear (en orden del curso)

- `01_state_graph.py` — primer grafo de estado básico
- `02_messages_graph.py` — grafo con historial de mensajes
- `03_tool_binding.py` — grafo con herramientas
- `04_react_agent.py` — ReAct completo con LangGraph
- `05_parallel_workflow.py` — nodos en paralelo
- `06_routing_workflow.py` — bifurcaciones condicionales
- `07_orchestrator_worker.py` — orquestador con workers
- `08_memory.py` — memoria persistente entre conversaciones
- `09_human_in_the_loop.py` — confirmación humana en el flujo

---

## Instalación
```bash
uv add langgraph
```

## Recursos
- [LangGraph Docs](https://langchain-ai.github.io/langgraph/)
- [LangGraph conceptos](https://langchain-ai.github.io/langgraph/concepts/)
