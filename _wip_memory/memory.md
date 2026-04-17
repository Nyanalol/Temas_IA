# WIP — Memory (Memoria en agentes y chatbots)

Por defecto un LLM no recuerda nada entre llamadas: cada `invoke()` es independiente. La **memoria** resuelve esto manteniendo el historial de la conversación y pasándolo en cada turno.

---

## Qué aprenderás aquí

### 1. El problema sin memoria
```
Usuario: Me llamo Miguel.
IA: Hola Miguel.
Usuario: ¿Cómo me llamo?
IA: No sé tu nombre.  ← no recuerda
```

### 2. Pasar el historial manualmente
La forma más básica: acumular los mensajes y pasarlos todos en cada llamada.
```python
historial = [SystemMessage("Eres un asistente.")]
historial.append(HumanMessage("Me llamo Miguel"))
historial.append(AIMessage(respuesta.content))
historial.append(HumanMessage("¿Cómo me llamo?"))
respuesta = llm.invoke(historial)
```

### 3. ConversationBufferMemory
LangChain gestiona el historial automáticamente. Guarda todos los mensajes (puede volverse muy grande).

### 4. ConversationSummaryMemory
En lugar de guardar todos los mensajes, resume la conversación pasada. Útil para conversaciones largas que no caben en el contexto del modelo.

### 5. Memoria persistente
Guardar el historial en disco (JSON, SQLite) para que sobreviva entre sesiones.

### 6. LangGraph y memoria de agentes
LangGraph es el framework moderno de LangChain para agentes con memoria de estado. Es más potente que el `AgentExecutor` clásico.

---

## Ideas de scripts a crear

- `sin_memoria.py` — demostrar el problema
- `historial_manual.py` — acumular mensajes a mano
- `buffer_memory.py` — ConversationBufferMemory
- `summary_memory.py` — ConversationSummaryMemory
- `memoria_persistente.py` — guardar/cargar historial en JSON

---

## Recursos
- [LangChain Memory](https://python.langchain.com/docs/concepts/memory/)
- [LangGraph](https://langchain-ai.github.io/langgraph/)
