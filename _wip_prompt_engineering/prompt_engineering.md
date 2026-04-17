# WIP — Prompt Engineering

El prompt engineering es el arte de hablarle bien a un LLM para obtener las respuestas que necesitas. Antes de añadir agentes o herramientas complejas, es fundamental dominar esto: un buen prompt vale más que un modelo más grande.

> **Cubierto en el curso de LangChain:**
> - `1:38:24` Prompts Templates Functions
> - `1:54:59` Pydantic & TypedDict for Structured Output
>
> Los scripts de esta carpeta complementan esas secciones con experimentos propios.

---

## Qué aprenderás aquí

### 1. Zero-shot vs Few-shot
- **Zero-shot**: le preguntas directamente sin ejemplos.
- **Few-shot**: le das 2-3 ejemplos de input/output antes de la pregunta real.
  El modelo "imita" el patrón que le has mostrado.

### 2. Chain-of-Thought (CoT)
Añadir "piensa paso a paso" al prompt mejora drásticamente las respuestas en tareas de razonamiento. El modelo genera sus pasos intermedios antes de dar la respuesta final.

### 3. PromptTemplate de LangChain
LangChain tiene `PromptTemplate` y `ChatPromptTemplate` para parametrizar prompts con variables:
```python
from langchain_core.prompts import ChatPromptTemplate

template = ChatPromptTemplate.from_messages([
    ("system", "Eres un experto en {dominio}."),
    ("human",  "{pregunta}"),
])
prompt = template.invoke({"dominio": "Python", "pregunta": "¿Qué es un decorator?"})
```

### 4. Structured Output — Pydantic y TypedDict
¿Cómo hacer que el LLM devuelva JSON con una estructura fija?
```python
from pydantic import BaseModel

class Resumen(BaseModel):
    titulo: str
    puntos_clave: list[str]

llm_structured = llm.with_structured_output(Resumen)
resultado = llm_structured.invoke("Resume este texto...")
print(resultado.titulo)
```

### 5. ReAct (Reason + Act)
Patrón donde el LLM razona, decide actuar (llamar a una herramienta), observa el resultado, y vuelve a razonar. Es la base de los agentes modernos. Ver `_wip_tools/`.

### 6. Prompt para RAG
Cómo estructurar el prompt del pipeline RAG para que el modelo solo use el contexto recuperado y no invente información (reducir alucinaciones).

---

## Ideas de scripts a crear

- `zero_shot_vs_few_shot.py` — comparar respuestas con y sin ejemplos
- `chain_of_thought.py` — tareas matemáticas o de razonamiento
- `prompt_templates.py` — uso de ChatPromptTemplate con variables
- `structured_output.py` — Pydantic y TypedDict para output estructurado
- `rag_prompt.py` — refinar el prompt del pipeline RAG

---

## Recursos
- [LangChain Prompt Templates](https://python.langchain.com/docs/concepts/prompt_templates/)
- [Guía de Anthropic sobre prompting](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview)
- [OpenAI Prompt Engineering guide](https://platform.openai.com/docs/guides/prompt-engineering)
