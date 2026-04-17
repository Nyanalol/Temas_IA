# WIP — Evaluation (Evaluación de sistemas RAG y LLMs)

Construir un RAG es la mitad del trabajo. La otra mitad es saber si funciona bien. Sin métricas, no sabes si tus cambios mejoran o empeoran el sistema.

---

## Qué aprenderás aquí

### 1. El problema de evaluar LLMs
Las respuestas son texto libre, no hay un valor exacto correcto. Se necesitan métricas específicas o usar otro LLM como juez.

### 2. Métricas para RAG — RAGAS

[RAGAS](https://docs.ragas.io) es el framework estándar para evaluar pipelines RAG. Mide:

| Métrica | Qué mide |
|---|---|
| **Faithfulness** | ¿La respuesta está basada en el contexto recuperado? (detecta alucinaciones) |
| **Answer Relevancy** | ¿La respuesta es pertinente a la pregunta? |
| **Context Precision** | ¿Los chunks recuperados son relevantes? |
| **Context Recall** | ¿Se recuperó todo lo necesario para responder? |

### 3. LLM-as-a-judge
Usar un LLM para evaluar la respuesta de otro LLM. Se le da la pregunta, el contexto y la respuesta, y puntúa de 1 a 5 con explicación.

### 4. Crear un test set
Para evaluar necesitas un conjunto de preguntas con respuestas esperadas sobre tus documentos. Esto se puede generar con el propio LLM a partir de los documentos.

### 5. Comparar configuraciones
Evaluar cómo afectan los cambios al sistema:
- Chunk size diferente
- Otro modelo de embeddings
- Más/menos documentos recuperados (k)
- Diferente prompt

---

## Ideas de scripts a crear

- `generar_test_set.py` — generar preguntas/respuestas a partir de documentos
- `evaluar_ragas.py` — evaluar el pipeline RAG con RAGAS
- `llm_as_judge.py` — usar un LLM para puntuar respuestas
- `comparar_configuraciones.py` — benchmark de diferentes setups del RAG

---

## Recursos
- [RAGAS](https://docs.ragas.io)
- [LangChain Evaluation](https://python.langchain.com/docs/guides/evaluation/)
- [OpenAI Evals](https://github.com/openai/evals)
