# WIP — RAG Avanzado

El pipeline básico de RAG (cargar documentos → embeddings → similarity search → respuesta) ya está cubierto en `rag/`. Pero hay muchas técnicas avanzadas que mejoran drásticamente la calidad de la recuperación y reducen las alucinaciones.

> Esta carpeta complementa `rag/`. Los scripts avanzados irán aquí para no mezclarlos con el pipeline base.

---

## Qué falta del RAG básico

### 1. Multi-Query Retriever
El problema: si tu pregunta está mal formulada, no se recuperan los documentos correctos.
La solución: generar automáticamente 3-5 variaciones de la pregunta con el LLM, buscar con cada una, y combinar los resultados.

```python
from langchain.retrievers import MultiQueryRetriever
retriever = MultiQueryRetriever.from_llm(vectorstore.as_retriever(), llm)
```

### 2. HyDE — Hypothetical Document Embeddings
En lugar de buscar con la pregunta directamente, se pide al LLM que invente un documento hipotético que respondería a la pregunta. Ese documento (más similar a los documentos reales) se usa para buscar.

### 3. Re-ranking
Después de recuperar los top-k documentos, se aplica un segundo modelo (más potente) que reordena los resultados por relevancia real. Los más usados: Cohere Rerank, BGE Reranker.

### 4. Hybrid Search — BM25 + Semántico
La búsqueda por embeddings es buena con similitud semántica pero falla con términos exactos (nombres propios, códigos, siglas). BM25 es el algoritmo clásico de búsqueda por palabras clave. Combinarlos (Hybrid Search con EnsembleRetriever) da lo mejor de los dos mundos.

```python
from langchain.retrievers import EnsembleRetriever, BM25Retriever
```

### 5. Parent Document Retriever
Los chunks pequeños son malos para el contexto pero buenos para la búsqueda. Los chunks grandes son buenos para el contexto pero malos para la búsqueda.
Solución: indexar chunks pequeños para buscar, pero devolver el chunk padre (grande) como contexto al LLM.

### 6. Self-Query Retriever
El LLM interpreta la pregunta y genera tanto la query semántica como filtros de metadatos:
> "Dame documentos de tipo PDF del desarrollador MA" → busca por embedding + filtra `type=pdf, developer=MA`

### 7. Contextual Compression
Después de recuperar los documentos, se comprimen para quedarse solo con las partes relevantes a la pregunta. Evita pasar contexto irrelevante al LLM.

### 8. RAGAS — Evaluación del RAG
Medir si el RAG funciona bien. Ver `_wip_evaluation/` para el detalle.

---

## Ideas de scripts a crear

- `multi_query.py` — MultiQueryRetriever
- `hyde.py` — Hypothetical Document Embeddings
- `hybrid_search.py` — BM25 + semántico con EnsembleRetriever
- `reranking.py` — Cohere Rerank o BGE
- `parent_document.py` — Parent Document Retriever

---

## Recursos
- [LangChain RAG How-To](https://python.langchain.com/docs/how_to/#qa-with-rag)
- [Advanced RAG techniques (Pinecone)](https://www.pinecone.io/learn/advanced-rag/)
