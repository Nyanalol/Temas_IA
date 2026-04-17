# WIP — Fine-tuning

El fine-tuning adapta un modelo preentrenado a tu dominio concreto con tus propios datos. Es un paso avanzado: antes de llegar aquí asegúrate de que el RAG y el prompt engineering no son suficientes (suelen serlo).

---

## Qué aprenderás aquí

### 1. ¿Cuándo tiene sentido hacer fine-tuning?
- El modelo no entiende el vocabulario o formato específico de tu dominio.
- Necesitas un estilo de respuesta muy concreto y consistente.
- Las respuestas deben ser muy cortas y el prompt engineering las hace largas.
- El RAG no es suficiente porque el conocimiento necesita estar "horneado" en el modelo.

### 2. Tipos de fine-tuning
- **Full fine-tuning** — actualiza todos los pesos. Requiere mucha GPU y datos.
- **LoRA / QLoRA** — solo entrena una pequeña fracción de parámetros añadidos. Es la técnica estándar hoy en día para hacerlo en hardware modesto.
- **Instruction tuning** — enseñar al modelo a seguir instrucciones en un formato concreto.

### 3. Preparar el dataset
El formato más habitual es JSONL con pares instrucción-respuesta:
```json
{"instruction": "Resume este texto:", "input": "...", "output": "..."}
```

### 4. Herramientas
- **Hugging Face `transformers` + `trl`** — librería estándar para fine-tuning.
- **Unsloth** — fine-tuning muy rápido y con menos VRAM.
- **LM Studio / Ollama** — para probar el modelo resultante en local.

### 5. Evaluar el modelo fine-tuneado
Comparar respuestas antes y después. Ver el módulo `_wip_evaluation/`.

---

## Ideas de scripts a crear

- `preparar_dataset.py` — convertir datos propios a formato JSONL
- `finetune_lora.py` — fine-tuning con LoRA usando `trl`
- `inferencia.py` — probar el modelo resultante
- `comparar_base_vs_finetuned.py` — evaluar la mejora

---

## Requisitos de hardware
Fine-tuning con LoRA en un modelo de 7B parámetros necesita aproximadamente 8-16 GB de VRAM (GPU). Con QLoRA se puede bajar a ~6 GB.

---

## Recursos
- [HuggingFace TRL (fine-tuning)](https://huggingface.co/docs/trl)
- [Unsloth](https://github.com/unslothai/unsloth)
- [LoRA paper](https://arxiv.org/abs/2106.09685)
