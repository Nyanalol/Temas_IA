# Asistente de Trabajo

Asistente personal orientado a búsqueda de empleo y gestión de carrera profesional.
Usa tu CV como contexto base (RAG sobre ChromaDB) y lo combina con tus proyectos actuales leídos desde Google Sheets.

---

## Funcionalidades actuales

| # | Skill | Qué hace |
|---|-------|----------|
| 1 | **Indexar CVs** | Lee los PDFs de `work/inputs/cv/` y los indexa en ChromaDB. Obligatorio antes de usar el resto. |
| 2 | **CV Q&A** | Responde preguntas en lenguaje natural sobre tu perfil, experiencia y skills. |
| 3 | **Recruiter Reply** | Recibe el mensaje de un recruiter de LinkedIn y genera una respuesta profesional basada en tu CV y reglas personalizadas. |
| 4 | **LinkedIn Optimizer** | Analiza tu perfil de LinkedIn (texto pegado), puntúa del 1 al 10 y propone mejoras por sección orientadas a ATS y recruiters. |
| 5 | **CV Updater → .docx** | Actualiza tu CV con nuevas instrucciones (proyectos, logros, skills) y exporta el resultado a un archivo Word listo para enviar. |
| 6 | **Google Sheets loader** | Lee una hoja de cálculo pública con tus proyectos y tareas actuales, y la usa como contexto adicional en las skills 3 y 5. |

Todos los archivos generados (respuestas, análisis, `.docx`) se guardan en `work/outputs/`.

---

## Requisitos previos

1. **CVs en PDF** — Cópialos en `work/inputs/cv/`. Nombra los archivos con `_es` o `_en` para que el idioma se detecte automáticamente:
   ```
   work/inputs/cv/cv_es.pdf
   work/inputs/cv/cv_en.pdf
   ```

2. **Variables de entorno** — Copia `.env.example` a `.env` y configura `LLM_PROVIDER`, `LLM_MODEL`, etc. (igual que el resto del proyecto).

3. **Google Sheet pública** (opcional) — Ve a tu hoja → *Compartir* → *Cualquier persona con el enlace puede ver*. La URL normal de Google Sheets se convierte automáticamente a exportación CSV.

---

## Ejecución

```bash
python -m work.main
```

Aparece el menú interactivo:

```
────────────────────────────────────────────────────────────
  ASISTENTE DE TRABAJO
────────────────────────────────────────────────────────────
  1. Indexar / actualizar CVs
  2. Preguntar sobre mi CV
  3. Responder mensaje de recruiter
  4. Optimizar perfil de LinkedIn
  5. Actualizar CV y exportar a Word (.docx)
  6. Cargar proyectos desde Google Sheets  [no cargada]
  0. Salir
────────────────────────────────────────────────────────────
```

**Orden recomendado la primera vez:**
1. Opción `6` — carga tu Google Sheet de proyectos (opcional pero recomendado)
2. Opción `1` — indexa tus CVs (solo necesario la primera vez o cuando cambies los PDFs)
3. Ya puedes usar cualquier otra opción

---

## Estructura del paquete

```
work/
├── main.py            # CLI con menú interactivo
├── chain_factory.py   # Cadenas LCEL: QA, recruiter_reply, linkedin_opt, cv_updater
├── cv_indexer.py      # Indexa PDFs en ChromaDB (work/chroma_db/)
├── cv_writer.py       # Genera archivos .docx desde el modelo CVDocument
├── sheets_loader.py   # Lee Google Sheet pública vía CSV export
├── models.py          # Pydantic: RecruiterReply, LinkedInOptimization, CVDocument
├── prompts.py         # Prompts del sistema para cada skill
├── parsers.py         # PydanticOutputParsers
├── runnables.py       # debug_step, json_cleaner, format_docs
├── inputs/cv/         # ← pon aquí tus CVs (ignorado por git)
└── outputs/           # ← archivos generados (ignorado por git)
```

---

## Outputs generados

| Archivo | Skill que lo genera |
|---------|---------------------|
| `outputs/recruiter_reply.txt` | Recruiter Reply |
| `outputs/linkedin_optimization.txt` | LinkedIn Optimizer |
| `outputs/cv_updated_ES.docx` | CV Updater (CV en español) |
| `outputs/cv_updated_EN.docx` | CV Updater (CV en inglés) |
