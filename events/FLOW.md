# Flujo completo del agente de calendario iCloud — Guía definitiva al 100%

> **Para quién es esto:** Un Data Engineer que conoce Python y quiere entender no solo "qué hace el código" sino **por qué está estructurado así**, qué conceptos de IA/LangChain aplica en cada paso, y por qué se tomó cada decisión de diseño. Al terminar de leer deberías poder replicar este patrón para cualquier otra tarea de extracción de información con LLMs — y entender exactamente qué pasa cuando algo falla.

---

## Índice

1. [Visión general del sistema](#1-visión-general-del-sistema)
2. [Punto de entrada: `main.py` (consola) y `api.py` (iPhone)](#2-punto-de-entrada-mainpy-consola-y-apipy-iphone)
3. [La cadena LangChain: `chain_factory.py`](#3-la-cadena-langchain-chain_factorypy)
4. [El modelo de datos: `models.py`](#4-el-modelo-de-datos-modelspy)
5. [El prompt: `prompts.py`](#5-el-prompt-promptspy)
6. [El LLM: `config.py`](#6-el-llm-configpy)
7. [La limpieza del JSON: `runnables.py` → `extract_json_text`](#7-la-limpieza-del-json-runnablespy--extract_json_text)
8. [El parser: `parsers.py`](#8-el-parser-parserspy)
9. [Convertir el modelo a diccionario: `runnables.py` → `build_event_dict`](#9-convertir-el-modelo-a-diccionario-runnablespy--build_event_dict)
10. [La integración con iCloud: `icloud.py`](#10-la-integración-con-icloud-icloudpy)
11. [La API REST: `api.py`](#11-la-api-rest-apipy)
12. [Despliegue en Render](#12-despliegue-en-render)
13. [Conceptos clave reutilizables](#13-conceptos-clave-reutilizables)

---

## 1. Visión general del sistema

### Qué hace

El sistema recibe una frase en lenguaje natural como *"Cita con el médico el viernes a las 9, duración 30 minutos, recuérdamelo 15 minutos antes"* y la convierte en un evento real dentro de tu calendario de Apple iCloud. Sin abrir la app del calendario, sin rellenar formularios — solo texto.

### Arquitectura de dos capas

```
Usuario (texto libre en español o inglés)
        │
        ▼
┌─────────────────────────────────────────────────────────┐
│                    CAPA IA (LangChain)                  │
│                                                         │
│  Prompt Template → LLM (GPT-4o-mini / Llama3 / etc.)   │
│       → JSON Cleaner → Pydantic Parser                  │
│                                                         │
│  Archivos: chain_factory.py, prompts.py, models.py,     │
│            parsers.py, runnables.py, config.py           │
│                                                         │
│  Resultado: objeto EventExtraction (Python, tipado)     │
└─────────────────────────┬───────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                 CAPA INTEGRACIÓN (iCloud)                │
│                                                         │
│  EventExtraction → dict Python → ICS (texto plano)      │
│       → CalDAV (HTTP PUT) → Apple iCloud                │
│                                                         │
│  Archivos: runnables.py (build_event_dict), icloud.py   │
└─────────────────────────────────────────────────────────┘
```

### Por qué esta separación

**Separación de responsabilidades (Single Responsibility Principle).** La capa de IA no sabe nada de iCloud, CalDAV, ni ICS. La capa de integración no sabe nada de LLMs, prompts ni LangChain. Esto tiene consecuencias prácticas reales:

- **Cambiar de proveedor LLM** (de OpenAI a Ollama, o a Anthropic): solo tocas `config.py`. Ni `icloud.py` ni `chain_factory.py` cambian.
- **Cambiar de calendario** (de iCloud a Google Calendar): solo reescribes `icloud.py`. La cadena de IA sigue produciendo el mismo `EventExtraction`.
- **Testear la IA sin iCloud**: invocas la cadena, obtienes el objeto `EventExtraction`, lo inspeccionas. No necesitas credenciales de Apple.
- **Testear iCloud sin IA**: construyes un dict a mano y llamas a `create_event()`.

Si mezclas ambas responsabilidades en un solo archivo, no puedes hacer ninguna de estas cosas sin tocar todo.

---

## 2. Punto de entrada: `main.py` (consola) y `api.py` (iPhone)

Hay dos formas de usar el sistema. Las dos hacen exactamente lo mismo internamente (construir la cadena → invocarla → crear evento), pero tienen interfaz diferente.

### 2.1 Modo consola: `events/main.py`

```bash
python -m events.main
```

**Para qué sirve:** Desarrollo y pruebas locales. Puedes hablarle directamente desde la terminal.

**Flujo línea por línea:**

#### Paso 1: Asegurar que Ollama esté arrancado

```python
def _ensure_ollama_running(timeout: int = 15) -> None:
    url = "http://127.0.0.1:11434"
    try:
        urllib.request.urlopen(url, timeout=2)  # ¿Ya está corriendo?
        return
    except Exception:
        pass

    print("Ollama no está arrancado, iniciando...")
    subprocess.Popen(
        ["ollama", "serve"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            urllib.request.urlopen(url, timeout=2)
            print("Ollama listo.\n")
            return
        except Exception:
            time.sleep(1)

    raise RuntimeError(f"Ollama no arrancó en {timeout}s.")
```

**Por qué hacemos esto:** Ollama es un servidor local que expone modelos de IA vía HTTP (puerto 11434). A diferencia de OpenAI (que es un servicio en la nube, siempre disponible), Ollama necesita estar corriendo en tu máquina. Esta función:
1. Primero comprueba si ya está corriendo haciendo un HTTP GET a `localhost:11434`.
2. Si no responde, lo arranca como proceso background con `subprocess.Popen`.
3. Espera hasta 15 segundos haciendo polling cada segundo.

**Por qué `subprocess.Popen` y no `subprocess.run`:** `Popen` lanza el proceso sin bloquearse (es non-blocking). `run` esperaría a que termine — y Ollama nunca "termina", es un servidor.

**Nota:** En modo API (producción en Render), esta función NO se llama porque usamos OpenAI como proveedor, no Ollama.

#### Paso 2: Construir la cadena

```python
chain = build_event_chain()
```

Se llama una sola vez al arrancar. La cadena es un objeto reutilizable — la misma instancia se usa para todas las invocaciones. Ver sección 3 para el detalle completo.

#### Paso 3: Bucle interactivo

```python
while True:
    user_input = input("\nTú: ").strip()

    if user_input.lower() in ("salir", "exit", "quit"):
        break

    # 1. Invocar la cadena de IA
    extracted = chain.invoke({"user_message": user_input})

    # 2. Mostrar preview
    _show_event_summary(extracted)

    # 3. Pedir confirmación
    confirm = input("\n¿Crear este evento? [s/N]: ").strip().lower()
    if confirm not in ("s", "si", "sí", "y", "yes"):
        print("Evento descartado.")
        continue

    # 4. Crear en iCloud
    event_dict = build_event_dict(extracted)
    url = create_event(event_dict)
    print(f"\nEvento creado correctamente.\nURL: {url}")
```

**Por qué pedimos confirmación antes de crear:** Los LLMs alucinan. Pueden poner una fecha equivocada, inventar un título distinto al que pediste, o interpretar "mañana" como el día incorrecto. Mostrar un preview y pedir confirmación es un **human-in-the-loop** — una práctica fundamental cuando un LLM controla acciones irreversibles. Sin esto, podrías acabar con eventos fantasma en tu calendario.

**Por qué `[s/N]` con N en mayúscula:** Convención de UX en terminales. La opción en mayúscula es la acción por defecto si pulsas Enter sin escribir nada. N mayúscula = por defecto NO crea. Es una protección extra contra acciones accidentales.

#### La función `_show_event_summary`

```python
def _show_event_summary(extracted) -> None:
    print("\n" + "─" * 60)
    print("  EVENTO EXTRAÍDO")
    print("─" * 60)
    print(f"  Título       : {extracted.title}")
    print(f"  Inicio       : {extracted.start}")
    print(f"  Fin          : {extracted.end}")
    if extracted.location:
        print(f"  Lugar        : {extracted.location}")
    if extracted.notes:
        print(f"  Notas        : {extracted.notes}")
    if extracted.all_day:
        print("  Todo el día  : Sí")
    if extracted.repeat_freq:
        print(f"  Repetición   : {extracted.repeat_freq} (cada {extracted.repeat_interval})")
        if extracted.repeat_byday:
            print(f"  Días         : {', '.join(extracted.repeat_byday)}")
        if extracted.repeat_count:
            print(f"  N.º veces    : {extracted.repeat_count}")
        if extracted.repeat_until:
            print(f"  Hasta        : {extracted.repeat_until}")
    if extracted.alarms:
        reminders = ", ".join(f"{a.trigger_minutes_before} min" for a in extracted.alarms)
        print(f"  Recordatorios: {reminders}")
    if extracted.categories:
        print(f"  Categorías   : {', '.join(extracted.categories)}")
    if extracted.calendar_name:
        print(f"  Calendario   : {extracted.calendar_name}")
    print("─" * 60)
```

**Por qué solo mostramos campos que no son None:** El modelo tiene ~20 campos, pero la mayoría son opcionales. Si el usuario dice "cena el viernes a las 9", solo title/start/end tendrán valor. Mostrar 15 líneas de "None" ensucia la salida y dificulta que el usuario verifique lo importante.

### 2.2 Modo API: `events/api.py`

```bash
uvicorn events.api:app --host 0.0.0.0 --port 8000
```

**Para qué sirve:** Producción. Es lo que corre en Render y lo que el iPhone (Shortcuts) llama via HTTP.

Es una API REST con FastAPI. Tiene tres endpoints:

| Endpoint | Método | Auth | Descripción |
|---|---|---|---|
| `/health` | GET | No | Devuelve `{"status": "ok"}`. Lo usa Render para saber si el servidor está vivo. |
| `/ping` | POST | No | Igual que health pero POST. Útil para "despertar" el servidor (los servicios gratuitos de Render se duermen tras 15 min de inactividad). |
| `/event` | POST | Sí (`X-API-Key`) | Recibe mensaje en natural, lo convierte en evento y lo crea en iCloud. |

El detalle completo de la API está en la [sección 11](#11-la-api-rest-apipy).

**Por qué FastAPI y no Flask:** Tres razones prácticas:
1. **Validación automática:** FastAPI usa Pydantic internamente. Si alguien envía un POST sin el campo `message`, FastAPI devuelve un error 422 con detalle, sin que escribas una línea de validación.
2. **Tipado nativo:** Los modelos `EventRequest` y `EventResponse` están tipados. El IDE te autocompleta, y en tiempo de ejecución se valida que los datos coincidan.
3. **Documentación auto-generada:** FastAPI genera Swagger/OpenAPI automáticamente (aunque en nuestro caso la deshabilitamos con `docs_url=None` por seguridad — no queremos exponer la documentación al público).

---

## 3. La cadena LangChain: `chain_factory.py`

**Archivo:** `events/chain_factory.py`

Este es el **corazón de toda la aplicación**. Aquí se ensamblan todos los componentes de IA en un pipeline.

### Código completo del archivo

```python
from config import get_llm
from .parsers import get_event_parser
from .prompts import get_extract_prompt
from .runnables import debug_step, get_json_cleaner


def build_event_chain():
    llm = get_llm()                          # 1. Obtener el LLM configurado
    parser = get_event_parser()              # 2. Crear el parser de Pydantic
    prompt = get_extract_prompt(             # 3. Crear el prompt con las instrucciones de formato
        parser.get_format_instructions()
    )
    json_cleaner = get_json_cleaner()        # 4. Crear el limpiador de JSON

    chain = (
        debug_step("INPUT")                  # A. Log de entrada
        | prompt                             # B. Formatear el prompt
        | debug_step("PROMPT")               # C. Log del prompt formateado
        | llm                                # D. Llamar al LLM
        | json_cleaner                       # E. Limpiar la salida
        | debug_step("JSON_CLEAN")           # F. Log del JSON limpio
        | parser                             # G. Parsear a Pydantic
        | debug_step("EXTRACTED_EVENT")      # H. Log del evento extraído
    )

    return chain
```

### Qué es una cadena LCEL (LangChain Expression Language)

El operador `|` aquí **NO** es el OR bitwise de Python. LangChain lo sobreescribe (via `__or__` / `__ror__` en la clase base `Runnable`) para que signifique **composición secuencial**: la salida de la izquierda se pasa como entrada a la derecha.

Es idéntico conceptualmente a un pipeline Unix:
```bash
cat archivo.txt | grep "error" | sort | uniq
```

Cada componente de la cadena implementa la interfaz `Runnable` de LangChain, que exige un método `.invoke(input) → output`. Cuando haces `chain.invoke({"user_message": "..."})`, LangChain ejecuta cada paso en orden, pasando la salida de uno como entrada del siguiente.

### Flujo paso a paso con tipos exactos

Vamos a trazar exactamente qué entra y qué sale de cada paso cuando el usuario escribe *"Cita con el médico el viernes a las 9"*:

```
PASO A — debug_step("INPUT")
  Entrada: {"user_message": "Cita con el médico el viernes a las 9"}
  Qué hace: Loguea el diccionario con logger.debug(). No modifica nada.
  Salida:  {"user_message": "Cita con el médico el viernes a las 9"}
  Tipo:    dict → dict (pass-through)

PASO B — prompt (ChatPromptTemplate)
  Entrada: {"user_message": "Cita con el médico el viernes a las 9"}
  Qué hace: Sustituye {user_message} en el template. {format_instructions}
            ya fue rellenado con .partial() al construir el prompt.
  Salida:  ChatPromptValue conteniendo dos mensajes:
           - SystemMessage: "You are a calendar assistant... Today's date is 2026-04-21..."
           - HumanMessage: "Create a calendar event based on this message:\n\n
                           Cita con el médico el viernes a las 9\n\n
                           Return only a valid JSON object following these instructions:\n
                           The output should be formatted as a JSON instance that conforms
                           to the JSON schema below... {campos del modelo con descripciones}"
  Tipo:    dict → ChatPromptValue

PASO C — debug_step("PROMPT")
  Entrada: ChatPromptValue (los mensajes formateados)
  Qué hace: Loguea todo el prompt que se va a enviar al LLM. Muy útil para
            depurar — puedes ver exactamente qué instrucciones recibe el modelo.
  Salida:  ChatPromptValue (sin modificar)
  Tipo:    ChatPromptValue → ChatPromptValue (pass-through)

PASO D — llm (ChatOpenAI / ChatOllama / ChatAnthropic / ChatGroq)
  Entrada: ChatPromptValue (los mensajes)
  Qué hace: Envía los mensajes al LLM vía HTTP. Espera la respuesta completa.
            Esta es la llamada más lenta de toda la cadena (~0.5-3 segundos
            dependiendo del modelo y proveedor).
  Salida:  AIMessage(content='{"title": "Médico", "start": "2026-04-25T09:00:00", ...}')
  Tipo:    ChatPromptValue → AIMessage

PASO E — json_cleaner (RunnableLambda wrapping extract_json_text)
  Entrada: AIMessage con el texto del LLM
  Qué hace: Extrae el JSON de la respuesta del LLM. Puede que el LLM haya
            devuelto el JSON envuelto en markdown (```json ... ```), con texto
            antes o después, etc. Esta función lo limpia.
  Salida:  '{"title": "Médico", "start": "2026-04-25T09:00:00", ...}'
  Tipo:    AIMessage → str (JSON puro)

PASO F — debug_step("JSON_CLEAN")
  Entrada: String JSON limpio
  Qué hace: Loguea el JSON antes de parsearlo. Si el parsing falla después,
            este log te dice exactamente qué texto intentó parsear.
  Salida:  String JSON limpio (sin modificar)
  Tipo:    str → str (pass-through)

PASO G — parser (PydanticOutputParser[EventExtraction])
  Entrada: String JSON
  Qué hace: json.loads() → valida contra el esquema de EventExtraction →
            construye la instancia de Pydantic. Si algún campo obligatorio
            falta o un tipo no coincide, lanza OutputParserException.
  Salida:  EventExtraction(title="Médico", start="2026-04-25T09:00:00",
                           end="2026-04-25T10:00:00", location=None, ...)
  Tipo:    str → EventExtraction

PASO H — debug_step("EXTRACTED_EVENT")
  Entrada: EventExtraction
  Qué hace: Loguea el objeto Pydantic final. Puedes ver todos los campos
            que el LLM rellenó y cuáles quedaron como None/default.
  Salida:  EventExtraction (sin modificar)
  Tipo:    EventExtraction → EventExtraction (pass-through)
```

### Por qué los `debug_step` intercalados

Los pasos de debug son **`RunnableLambda`** que loguean y devuelven el input sin tocarlo. Están en `events/runnables.py`:

```python
def debug_step(name: str) -> RunnableLambda:
    def _debug(x):
        logger.debug("=" * 60)
        logger.debug("STEP %s", name)
        logger.debug("%s", x)
        return x
    return RunnableLambda(_debug)
```

**Por qué los necesitamos:** Cuando la cadena falla (y fallará — los LLMs son impredecibles), necesitas saber **en qué paso falló y con qué datos**. Sin estos debug steps, solo ves el error final. Con ellos, puedes ver:
- ¿El prompt se formateó bien? → Log `PROMPT`
- ¿El LLM devolvió JSON válido? → Log `JSON_CLEAN`
- ¿El parser logró crear el objeto? → Log `EXTRACTED_EVENT`

Usan `logger.debug()`, así que **no aparecen en producción** (donde el nivel de log es INFO o WARNING). Solo se ven cuando activas logging DEBUG en desarrollo.

### Concepto clave — `RunnableLambda`

`RunnableLambda` es un wrapper de LangChain que convierte cualquier función Python `f(x) → y` en un `Runnable` composable con `|`. Sin `RunnableLambda`, no podrías meter funciones custom dentro de la cadena LCEL.

```python
# Esto NO funciona (una función normal no es un Runnable):
chain = prompt | llm | mi_funcion | parser  # ❌ Error

# Esto SÍ funciona:
chain = prompt | llm | RunnableLambda(mi_funcion) | parser  # ✅
```

### Concepto clave — Lazy init en la API

En `api.py`, la cadena NO se construye al importar el módulo. Se construye la primera vez que llega un request:

```python
_chain = None  # Variable de módulo

def _get_chain():
    global _chain
    if _chain is None:
        _chain = build_event_chain()  # Se ejecuta solo una vez
    return _chain
```

**Por qué:** Construir la cadena implica cargar `config.py`, conectar con el proveedor LLM, etc. Si lo haces en el import, el servidor tarda más en arrancar (cold start más largo en Render). Con lazy init, el servidor arranca rápido y la primera request es un poco más lenta, pero todas las siguientes reutilizan la misma cadena.

**Por qué un singleton global y no crear la cadena en cada request:** La cadena es stateless — no guarda historial ni contexto entre invocaciones. Crear una nueva instancia por request desperdiciaría CPU y memoria innecesariamente. El LLM client interno mantiene un pool de conexiones HTTP que se reutilizan.

---

## 4. El modelo de datos: `models.py`

**Archivo:** `events/models.py`

### Código completo

```python
from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field


class AlarmInput(BaseModel):
    trigger_minutes_before: int = Field(
        description="Minutes before the event to trigger the alarm, e.g. 10 or 30"
    )
    description: Optional[str] = Field(
        default=None,
        description="Alarm notification text. If omitted, the event title will be used.",
    )


class EventExtraction(BaseModel):
    title: str = Field(description="Short title of the event")
    start: str = Field(
        description=(
            "Event start datetime in ISO 8601 format (YYYY-MM-DDTHH:MM:SS). "
            "Resolve relative expressions like 'mañana', 'el martes' using today's date."
        )
    )
    end: str = Field(
        description=(
            "Event end datetime in ISO 8601 format. "
            "If not specified by the user, default to 1 hour after start."
        )
    )
    location: Optional[str] = Field(
        default=None, description="Physical location or address of the event"
    )
    notes: Optional[str] = Field(
        default=None, description="Additional notes or description"
    )
    all_day: Optional[bool] = Field(
        default=False,
        description="True only if the user explicitly says it is an all-day event",
    )
    repeat_freq: Optional[str] = Field(
        default=None,
        description="Recurrence frequency: DAILY, WEEKLY, MONTHLY, YEARLY, or null",
    )
    repeat_interval: Optional[int] = Field(
        default=1,
        description="Recurrence interval, e.g. 2 means every 2 weeks when freq is WEEKLY",
    )
    repeat_count: Optional[int] = Field(
        default=None, description="Total number of occurrences. Null means infinite."
    )
    repeat_until: Optional[str] = Field(
        default=None,
        description="Repeat until this date, ISO 8601. Null means no end date.",
    )
    repeat_byday: Optional[list[str]] = Field(
        default=None,
        description="Days of week for weekly recurrence: MO, TU, WE, TH, FR, SA, SU",
    )
    categories: Optional[list[str]] = Field(
        default=None, description="Event categories or tags, e.g. ['Salud', 'Personal']"
    )
    url: Optional[str] = Field(
        default=None, description="URL related to the event"
    )
    status: Optional[str] = Field(
        default="CONFIRMED",
        description="Event status: CONFIRMED, TENTATIVE, or CANCELLED",
    )
    transparency: Optional[str] = Field(
        default="OPAQUE",
        description="OPAQUE blocks time in calendar, TRANSPARENT does not",
    )
    alarms: Optional[list[AlarmInput]] = Field(
        default=None, description="List of reminders before the event"
    )
    calendar_name: Optional[str] = Field(
        default=None,
        description="Name of the target calendar. Null to use the default.",
    )
```

### Este modelo cumple DOS roles a la vez

#### Rol 1: Esquema de salida para el LLM

`PydanticOutputParser` (ver sección 8) lee este modelo y genera automáticamente un texto como:

```
The output should be formatted as a JSON instance that conforms to the JSON schema below.

As an example, for the schema {"properties": {"foo": {"title": "Foo", "description": "a list of strings", "type": "array", "items": {"type": "string"}}}, "required": ["foo"]}
the object {"foo": ["bar", "baz"]} is a well-formatted instance of the schema.

Here is the output schema:
{"properties": {"title": {"description": "Short title of the event", ...}, "start": {"description": "Event start datetime in ISO 8601 format...", ...}, ...}}
```

Este texto se inyecta en el prompt (sección 5) para que el LLM sepa exactamente qué JSON devolver.

**Por qué las descripciones están en inglés:** Los LLMs están entrenados mayoritariamente en inglés. Las instrucciones de formato en inglés producen resultados más consistentes que en español, especialmente con modelos locales (Llama, Mistral). El usuario habla en español, pero las instrucciones técnicas son en inglés.

**Por qué las descripciones son tan explícitas:** Cada `Field(description=...)` es literalmente lo que el LLM lee para decidir qué poner en ese campo. Si la descripción es vaga ("start time"), el LLM podría devolver "9 de la mañana" o "09:00" o "2026-04-25 09:00:00". Con la descripción explícita *"Event start datetime in ISO 8601 format (YYYY-MM-DDTHH:MM:SS)"*, el LLM entiende el formato exacto esperado.

#### Rol 2: Validación en tiempo de ejecución

Cuando el parser intenta crear un `EventExtraction` a partir del JSON del LLM, Pydantic verifica automáticamente:

- `title` es `str` y es obligatorio → si falta, `ValidationError`
- `start` es `str` y es obligatorio → si falta, `ValidationError`
- `repeat_freq` si existe debe ser `str` → si el LLM pone un número, `ValidationError`
- `alarms` si existe debe ser `list[AlarmInput]` → si la estructura interna no coincide, `ValidationError`

**Por qué esto importa:** Sin esta validación, un JSON malformado del LLM llegaría hasta `icloud.py` y fallaría allí — lejos de donde se originó el problema, con un error incomprensible. Con Pydantic, el error se detecta inmediatamente y dice exactamente qué campo falló y por qué.

### La subclase `AlarmInput`

```python
class AlarmInput(BaseModel):
    trigger_minutes_before: int = Field(
        description="Minutes before the event to trigger the alarm, e.g. 10 or 30"
    )
    description: Optional[str] = Field(
        default=None,
        description="Alarm notification text. If omitted, the event title will be used.",
    )
```

**Por qué es un modelo separado y no un dict:** Si `alarms` fuera `list[dict]`, el LLM podría devolver cualquier estructura de dict. Con un modelo Pydantic tipado, el LLM sabe que cada alarma necesita `trigger_minutes_before` (int), y Pydantic valida que así sea.

### Concepto clave — Structured Output / Information Extraction

Este patrón completo (modelo Pydantic + PydanticOutputParser + prompt con format_instructions) se llama **Structured Output** o **Information Extraction**. Es el patrón más usado en aplicaciones LLM del mundo real. Lo usarás cada vez que necesites sacar datos estructurados de texto libre: extraer datos de facturas, parsear CVs, clasificar tickets de soporte, etc.

---

## 5. El prompt: `prompts.py`

**Archivo:** `events/prompts.py`

### Código completo

```python
import os
from datetime import date
from langchain_core.prompts import ChatPromptTemplate

_DEFAULT_CALENDAR = os.getenv("ICLOUD_DEFAULT_CALENDAR", "Cari y Cosi")


def get_extract_prompt(format_instructions: str) -> ChatPromptTemplate:
    today = date.today().isoformat()

    return ChatPromptTemplate.from_messages([
        (
            "system",
            (
                "You are a calendar assistant. "
                "The user will describe an event in natural language (possibly in Spanish). "
                "Extract all relevant event fields and return only a valid JSON object. "
                "Do not add explanations, markdown, or any text outside the JSON.\n\n"
                f"Today's date is {today}. "
                "Use it to resolve relative dates like 'mañana', 'el martes', "
                "'la próxima semana'.\n\n"
                "Rules:\n"
                "- If end time is not specified, set it to 1 hour after start.\n"
                "- If the user mentions reminders or recordatorios, extract them as alarms.\n"
                "- For recurring events, map the user's description to "
                "DAILY, WEEKLY, MONTHLY or YEARLY.\n"
                "- Only set all_day to true if the user explicitly says it is "
                "an all-day event.\n"
                f"- The default calendar is '{_DEFAULT_CALENDAR}'. "
                "Use it in calendar_name unless the user explicitly names a different one.\n"
                "- Leave optional fields as null if the user did not mention them."
            ),
        ),
        (
            "human",
            (
                "Create a calendar event based on this message:\n\n"
                "{user_message}\n\n"
                "Return only a valid JSON object following these instructions:\n"
                "{format_instructions}"
            ),
        ),
    ]).partial(format_instructions=format_instructions)
```

### Anatomía del prompt — pieza por pieza

#### El system message

El system message define **quién es** el LLM y **cómo debe comportarse**. Vamos línea por línea:

**`"You are a calendar assistant."`** — Establece el rol. Los LLMs responden mejor cuando tienen un rol claro. Sin esto, el modelo no sabe si debería ser formal, creativo, técnico...

**`"The user will describe an event in natural language (possibly in Spanish)."`** — Le dice al LLM que esperamos input en español. Sin esto, algunos modelos podrían confundirse con palabras como "mañana" (que en inglés significa "morning").

**`"Extract all relevant event fields and return only a valid JSON object."`** — Instrucción directa: tu output es JSON, nada más.

**`"Do not add explanations, markdown, or any text outside the JSON."`** — Refuerzo negativo. Los LLMs tienden a "explicar" su respuesta. Esta instrucción intenta minimizarlo (aunque no lo garantiza — por eso tenemos el `json_cleaner`).

**`f"Today's date is {today}."`** — **CRÍTICO.** Sin esta línea, el sistema no funciona correctamente. Los LLMs no saben qué día es hoy — su conocimiento se congeló en la fecha de entrenamiento. Cuando el usuario dice "mañana" o "el viernes", el LLM necesita saber la fecha actual para calcular la fecha correcta. `date.today().isoformat()` produce algo como `"2026-04-21"`.

**Las reglas de negocio:**
- *"If end time is not specified, set it to 1 hour after start"* — Regla por defecto. Sin esto, el LLM a veces devolvería `end: null` y la creación del evento fallaría.
- *"If the user mentions reminders or recordatorios, extract them as alarms"* — Mapeo lingüístico: "recuérdamelo" en español → campo `alarms` en el JSON.
- *"Only set all_day to true if the user explicitly says it is an all-day event"* — Restricción. Sin esto, el LLM a veces marca `all_day: true` cuando el usuario dice algo como "todo el día de la boda" (que no significa all-day event).
- *"The default calendar is '...'"* — Evita que el LLM invente un nombre de calendario.
- *"Leave optional fields as null if the user did not mention them"* — Evita que el LLM "rellene" campos inventando datos. Sin esto, podrías encontrar `location: "Office"` cuando el usuario nunca mencionó un lugar.

#### El human message

```
"Create a calendar event based on this message:\n\n"
"{user_message}\n\n"
"Return only a valid JSON object following these instructions:\n"
"{format_instructions}"
```

Dos variables de template:
- `{user_message}` — Se rellena en cada invocación con el texto del usuario.
- `{format_instructions}` — Se pre-rellena con `.partial()` al construir el prompt. Contiene el esquema JSON generado por `PydanticOutputParser`.

#### Por qué `.partial()` y no pasar ambas variables en `.invoke()`

```python
.partial(format_instructions=format_instructions)
```

`format_instructions` es el mismo texto para TODAS las invocaciones (describe el esquema del modelo, que no cambia). Solo `user_message` cambia por request. Al hacer `.partial()`, "fijamos" `format_instructions` en el template y la cadena solo necesita recibir `{"user_message": "..."}` al invocarse.

Esto es exactamente como `functools.partial` de Python:
```python
# Equivalente conceptual:
from functools import partial
greet = partial(print, "Hola")  # Fija el primer argumento
greet("Miguel")  # → "Hola Miguel"
```

### Por qué las format_instructions van al final del human message

Las instrucciones de formato se ponen en el human message (no en el system message) y al final (después del texto del usuario). Esto es deliberado:

1. **Posición reciente = más atención:** Los LLMs (especialmente los basados en transformer) prestan más atención al texto reciente (recency bias). Poner las instrucciones de formato al final maximiza la probabilidad de que el modelo las siga.

2. **Separación de preocupaciones en el prompt:** El system message define el comportamiento general. El human message contiene la tarea específica. Las instrucciones de formato son parte de la tarea, no del comportamiento general.

---

## 6. El LLM: `config.py`

**Archivo:** `config.py` (en la raíz del proyecto, NO en `events/`)

### Código completo

```python
import os
from dotenv import load_dotenv

load_dotenv()

LLM_PROVIDER    = os.getenv("LLM_PROVIDER",    "ollama")
LLM_MODEL       = os.getenv("LLM_MODEL",       "llama3")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0"))

EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "ollama")
EMBEDDING_MODEL    = os.getenv("EMBEDDING_MODEL",    "nomic-embed-text")


def get_llm():
    print(f"[config] LLM → proveedor={LLM_PROVIDER}  modelo={LLM_MODEL}")

    if LLM_PROVIDER == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(model=LLM_MODEL, temperature=LLM_TEMPERATURE)

    if LLM_PROVIDER == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=LLM_MODEL,
            temperature=LLM_TEMPERATURE,
            api_key=os.getenv("OPENAI_API_KEY"),
        )

    if LLM_PROVIDER == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model=LLM_MODEL,
            temperature=LLM_TEMPERATURE,
            api_key=os.getenv("ANTHROPIC_API_KEY"),
        )

    if LLM_PROVIDER == "groq":
        from langchain_groq import ChatGroq
        return ChatGroq(
            model=LLM_MODEL,
            temperature=LLM_TEMPERATURE,
            api_key=os.getenv("GROQ_API_KEY"),
        )

    raise ValueError(f"LLM_PROVIDER desconocido: '{LLM_PROVIDER}'")
```

### Por qué está en la raíz y no en `events/`

`config.py` se usa por `events/` y potencialmente por `agents/`, `rag/`, y otros módulos. Si estuviera dentro de `events/`, los otros módulos tendrían una dependencia cruzada. Al estar en la raíz, es un módulo compartido — cualquier paquete puede importar `from config import get_llm`.

### Por qué los imports son lazy (dentro de los `if`)

```python
if LLM_PROVIDER == "openai":
    from langchain_openai import ChatOpenAI  # ← Import dentro del if
    return ChatOpenAI(...)
```

Si los imports estuvieran al inicio del archivo:
```python
from langchain_ollama import ChatOllama    # Se ejecuta siempre
from langchain_openai import ChatOpenAI    # Se ejecuta siempre
from langchain_anthropic import ChatAnthropic  # Se ejecuta siempre
```

Entonces necesitarías tener instalados TODOS los paquetes (`langchain-ollama`, `langchain-openai`, `langchain-anthropic`, `langchain-groq`) incluso si solo usas uno. Con imports lazy, solo se importa el paquete del proveedor activo. Si usas OpenAI, no necesitas tener `langchain-ollama` instalado.

### Variables de entorno y valores por defecto

```python
LLM_PROVIDER    = os.getenv("LLM_PROVIDER",    "ollama")   # Default: ollama
LLM_MODEL       = os.getenv("LLM_MODEL",       "llama3")   # Default: llama3
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0")) # Default: 0
```

- **En local** (sin `.env` o con `.env` configurado para Ollama): usa Ollama + Llama3.
- **En Render** (con env vars en el dashboard): usa OpenAI + GPT-4o-mini.

**Por qué `temperature=0`:** Temperature controla la aleatoriedad del LLM.
- **`temperature=0`:** El modelo elige siempre el token más probable. La respuesta es determinista (o casi — hay floating point noise). Ideal para tareas de extracción donde la respuesta correcta es objetiva.
- **`temperature=0.7-1.0`:** El modelo muestrea tokens con probabilidad proporcional a su score. Produce respuestas variadas y "creativas". Peligroso para extracción porque introduce variabilidad donde no la queremos.

Para nuestro caso (extraer título, fecha, hora de un texto), queremos `temperature=0`. Si el usuario dice "médico el viernes a las 9", la respuesta correcta es siempre `{"title": "Médico", "start": "2026-04-25T09:00:00"}`. No hay espacio para "creatividad".

### Concepto clave — Abstracción de proveedores

`ChatOllama`, `ChatOpenAI`, `ChatAnthropic` y `ChatGroq` todos implementan la interfaz `BaseChatModel` de LangChain. Esto significa que la cadena `prompt | llm | parser` funciona **idénticamente** sin importar cuál uses. LangChain actúa como una capa de abstracción sobre las APIs de cada proveedor (que son todas distintas: OpenAI usa una API REST, Ollama otra, Anthropic otra).

```python
# Todos producen el mismo tipo de salida: AIMessage
llm = ChatOpenAI(model="gpt-4o-mini")
result = llm.invoke(messages)  # → AIMessage(content="...")

llm = ChatOllama(model="llama3")
result = llm.invoke(messages)  # → AIMessage(content="...")  ← misma interfaz
```

---

## 7. La limpieza del JSON: `runnables.py` → `extract_json_text`

**Archivo:** `events/runnables.py`

### Código de la función

```python
def extract_json_text(model_output) -> str:
    text = (
        model_output.content
        if hasattr(model_output, "content")
        else str(model_output)
    )
    text = text.strip()
    logger.debug("RAW_LLM_OUTPUT: %s", text)

    # Intento 1: el texto ya es JSON válido tal cual
    try:
        json.loads(text)
        return text
    except Exception:
        pass

    # Intento 2: extraer JSON con regex
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        candidate = match.group(0)
        json.loads(candidate)  # Verificar que es JSON válido
        logger.debug("JSON extracted with regex")
        return candidate

    raise ValueError(f"No valid JSON found in model output:\n{text}")
```

### Por qué existe este paso

Aunque el prompt dice claramente "devuelve solo JSON", los LLMs **no siempre obedecen**. Ejemplos reales de salida:

**Caso 1 — JSON limpio (ideal):**
```
{"title": "Médico", "start": "2026-04-25T09:00:00", ...}
```
→ `json.loads()` funciona directamente. La función devuelve el texto tal cual.

**Caso 2 — JSON envuelto en markdown (muy común con modelos locales):**
```
Here is the JSON for your event:

```json
{"title": "Médico", "start": "2026-04-25T09:00:00", ...}
```

I've set the default duration to 1 hour.
```
→ `json.loads()` falla (hay texto antes y después). La regex `r"\{.*\}"` con `re.DOTALL` extrae el bloque `{...}` y lo devuelve.

**Caso 3 — El LLM divaga completamente:**
```
Sure! I'd be happy to help you create a calendar event. However, I need more information...
```
→ `json.loads()` falla, la regex no encuentra `{...}` con JSON válido. Se lanza `ValueError`.

### Por qué `re.DOTALL`

La flag `re.DOTALL` hace que el `.` en la regex también coincida con `\n` (saltos de línea). Sin esta flag, `\{.*\}` solo coincidiría con JSON en una sola línea. Los JSON multi-línea (que es lo que devuelven la mayoría de LLMs) no se capturarían.

### Por qué `hasattr(model_output, "content")`

Normalmente el LLM devuelve un `AIMessage` (que tiene `.content`). Pero si alguien reutiliza `extract_json_text` en otro contexto donde la entrada ya es un string, la función no se rompe gracias al fallback `str(model_output)`.

### El wrapper para la cadena LCEL

```python
def get_json_cleaner() -> RunnableLambda:
    return RunnableLambda(extract_json_text)
```

**Por qué un wrapper:** `extract_json_text` es una función Python normal. Para usarla dentro de una cadena LCEL (con `|`), necesita ser un `Runnable`. `RunnableLambda` la envuelve.

---

## 8. El parser: `parsers.py`

**Archivo:** `events/parsers.py`

### Código completo

```python
from langchain_core.output_parsers import PydanticOutputParser
from .models import EventExtraction


def get_event_parser() -> PydanticOutputParser:
    return PydanticOutputParser(pydantic_object=EventExtraction)
```

### Qué hace `PydanticOutputParser` internamente

Este parser tiene dos caras:

#### Cara 1: Generación de instrucciones (antes de invocar el LLM)

```python
parser = get_event_parser()
instructions = parser.get_format_instructions()
# → "The output should be formatted as a JSON instance that conforms to the
#    JSON schema below.\n\nAs an example, for the schema {\"properties\":
#    {\"foo\": ...}} ...\n\nHere is the output schema:\n{\"properties\":
#    {\"title\": {\"description\": \"Short title of the event\", ...}, ...}}"
```

Esto lee TODOS los campos de `EventExtraction`, sus tipos y sus `description`, y genera un texto en lenguaje natural que describe el esquema JSON esperado. Este texto se inyecta en el prompt para que el LLM sepa qué devolver.

#### Cara 2: Parsing de la respuesta (después de invocar el LLM)

```python
result = parser.invoke('{"title": "Médico", "start": "2026-04-25T09:00:00", ...}')
# → EventExtraction(title="Médico", start="2026-04-25T09:00:00", ...)
```

Internamente hace:
1. `json.loads(text)` → convierte el string JSON en un dict Python.
2. `EventExtraction(**parsed_dict)` → construye el objeto Pydantic, validando tipos.

Si la validación falla, lanza `OutputParserException` con un mensaje descriptivo que incluye el JSON que recibió y qué validación falló.

### Concepto clave — Otros Output Parsers de LangChain

| Parser | Salida | Cuándo usarlo |
|---|---|---|
| `StrOutputParser` | `str` | Cuando solo quieres el texto crudo del LLM (chatbots, resúmenes) |
| `JsonOutputParser` | `dict` | Cuando quieres JSON pero sin validación de esquema |
| `PydanticOutputParser` | Objeto Pydantic tipado | Cuando necesitas datos estructurados y validados (nuestro caso) |
| `CommaSeparatedListOutputParser` | `list[str]` | Cuando pides una lista simple al LLM |

**Por qué elegimos `PydanticOutputParser`:** Combina parsing + validación + generación de instrucciones en un solo componente. Es el más robusto para extracción de datos.

---

## 9. Convertir el modelo a diccionario: `runnables.py` → `build_event_dict`

**Archivo:** `events/runnables.py`

### Código completo

```python
MADRID = ZoneInfo("Europe/Madrid")
_DEFAULT_CALENDAR = os.getenv("ICLOUD_DEFAULT_CALENDAR", "Cari y Cosi")


def _parse_dt(iso_str: str) -> datetime:
    dt = datetime.fromisoformat(iso_str)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=MADRID)
    return dt


def build_event_dict(extracted: EventExtraction) -> dict:
    event = {
        "title": extracted.title,
        "start": _parse_dt(extracted.start),
        "end": _parse_dt(extracted.end),
        "location": extracted.location or "",
        "notes": extracted.notes or "",
        "all_day": extracted.all_day or False,
        "repeat_freq": extracted.repeat_freq,
        "repeat_interval": extracted.repeat_interval or 1,
        "repeat_count": extracted.repeat_count,
        "repeat_until": None,
        "repeat_byday": extracted.repeat_byday,
        "categories": extracted.categories or [],
        "url": extracted.url or "",
        "status": extracted.status or "CONFIRMED",
        "transparency": extracted.transparency or "OPAQUE",
        "alarms": [],
        "calendar_name": extracted.calendar_name or _DEFAULT_CALENDAR,
    }

    if extracted.repeat_until:
        event["repeat_until"] = _parse_dt(extracted.repeat_until)

    if extracted.alarms:
        event["alarms"] = [
            {
                "action": "DISPLAY",
                "trigger_minutes_before": a.trigger_minutes_before,
                "description": a.description or extracted.title,
            }
            for a in extracted.alarms
        ]

    return event
```

### Por qué este paso existe (y no pasamos el Pydantic directamente a icloud.py)

Esta función es la **capa de transformación** entre la capa IA y la capa de integración. Sin ella, `icloud.py` tendría que saber qué es un `EventExtraction` — rompiendo la separación de responsabilidades.

Las transformaciones que hace:

1. **`str` ISO → `datetime` con timezone:** El LLM devuelve fechas como strings (`"2026-04-25T09:00:00"`). iCloud necesita `datetime` objects con timezone para poder convertir a UTC. La función `_parse_dt` hace esta conversión.

2. **None → valores por defecto:** Campos opcionales que el LLM dejó como `null` se convierten en valores seguros (`""`, `[]`, `False`, `"CONFIRMED"`) para que `icloud.py` no tenga que hacer null checks.

3. **Alarms: modelo Pydantic → dict plano:** Los objetos `AlarmInput` se convierten en dicts con la estructura que `icloud.py` espera, añadiendo el campo `action: "DISPLAY"` (que es un detalle del formato ICS, no algo que el LLM necesite saber).

4. **Calendario por defecto:** Si el LLM devolvió `calendar_name: null`, se usa el calendario configurado en la variable de entorno `ICLOUD_DEFAULT_CALENDAR`.

### `_parse_dt` — El manejo de timezones

```python
def _parse_dt(iso_str: str) -> datetime:
    dt = datetime.fromisoformat(iso_str)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=MADRID)
    return dt
```

**El problema:** Los LLMs casi siempre devuelven fechas sin timezone: `"2026-04-25T09:00:00"`. Esto es un **datetime naive** — Python no sabe si son las 9:00 de Madrid, de Tokyo o de New York.

**La solución:** Si el datetime no tiene timezone (`dt.tzinfo is None`), asumimos Europe/Madrid. Cuando más adelante `icloud.py` convierta esto a UTC para el formato ICS, `09:00 Madrid` se convertirá correctamente a `07:00 UTC` (en horario de verano, UTC+2).

**Por qué `ZoneInfo` y no `pytz`:** `ZoneInfo` es parte de la librería estándar desde Python 3.9. `pytz` está deprecado y tiene una API confusa (requiere `.localize()` en lugar de `.replace()`). `ZoneInfo` se usa con `.replace()` directamente.

**Por qué `MADRID` es constante de módulo:** Se crea una vez al importar el módulo. Crear `ZoneInfo("Europe/Madrid")` implica leer la base de datos de timezones del sistema operativo — no es caro, pero es innecesario repetirlo en cada llamada.

---

## 10. La integración con iCloud: `icloud.py`

**Archivo:** `events/icloud.py`

Este archivo **no tiene absolutamente nada de IA**. Es integración pura con el protocolo CalDAV de Apple. Podría existir en un proyecto que no usara LLMs.

### 10.1 Variables de entorno

```python
ICLOUD_EMAIL          = os.getenv("ICLOUD_EMAIL", "")
ICLOUD_APP_PASSWORD   = os.getenv("ICLOUD_APP_PASSWORD", "")
CALDAV_URL            = os.getenv("ICLOUD_CALDAV_URL", "https://caldav.icloud.com")
DEFAULT_CALENDAR_NAME = os.getenv("ICLOUD_DEFAULT_CALENDAR", "")
```

La contraseña **NO** es tu contraseña de Apple ID. Es una **App-Specific Password**, un password de 16 caracteres que generas en [appleid.apple.com](https://appleid.apple.com) → Sign-In and Security → App-Specific Passwords. Apple las requiere para aplicaciones de terceros porque tu cuenta real puede tener 2FA, y las apps no saben manejar el segundo factor.

### 10.2 Helpers de formato

```python
def _clean(value) -> str:
    """Escapa caracteres especiales para ICS (RFC 5545)."""
    if value is None:
        return ""
    text = str(value)
    text = text.replace("\\", "\\\\")  # \ → \\
    text = text.replace("\n", "\\n")   # nueva línea → literal \n
    text = text.replace(",", "\\,")    # , → \,
    text = text.replace(";", "\\;")    # ; → \;
    return text
```

**Por qué escapar estos caracteres:** El formato ICS usa `,` y `;` como delimitadores de campos. Si el título del evento contiene una coma literal (ejemplo: "Reunión con Juan, Pedro y Ana"), sin escapar se interpretaría como múltiples valores. Lo mismo con `\n` y `\`.

```python
def _fmt_utc(dt: datetime) -> str:
    """datetime con timezone → string UTC para ICS."""
    return dt.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    # Ejemplo: 2026-04-25T09:00:00+02:00 → "20260425T070000Z"
```

**El flujo de conversión completo:**
1. El LLM devuelve `"2026-04-25T09:00:00"` (string, sin timezone)
2. `_parse_dt` convierte a `datetime(2026, 4, 25, 9, 0, tzinfo=Europe/Madrid)` (datetime, Madrid)
3. `_fmt_utc` convierte a `"20260425T070000Z"` (string, UTC, formato ICS)

**Por qué la Z al final:** La `Z` significa "Zulu time" = UTC. Es la convención de ICS para indicar que la hora está en UTC. Sin la Z, los clientes de calendario no sabrían en qué timezone interpretar la hora.

```python
def _fmt_date(dt: datetime) -> str:
    """Para eventos all-day: solo la fecha, sin hora."""
    return dt.strftime("%Y%m%d")
    # Ejemplo: "20260425"
```

Los eventos de todo el día usan `DTSTART;VALUE=DATE:20260425` (sin hora, sin Z). Si les pones hora, el cliente de calendario los muestra como eventos de 24h con hora específica, que no es lo que queremos.

```python
def _trigger(minutes_before: int) -> str:
    """Minutos → formato de duración ISO 8601 para VALARM."""
    hours   = minutes_before // 60
    minutes = minutes_before % 60
    if hours and minutes:
        return f"-PT{hours}H{minutes}M"
    if hours:
        return f"-PT{hours}H"
    return f"-PT{minutes}M"
    # 30 → "-PT30M"
    # 90 → "-PT1H30M"
    # 120 → "-PT2H"
```

**El signo negativo:** `-PT30M` significa "30 minutos ANTES del evento". El `-` indica que el trigger es relativo al inicio del evento hacia atrás. `PT30M` sin `-` significaría 30 minutos DESPUÉS del inicio.

### 10.3 Construcción del ICS

```python
def build_ics(event: dict) -> str:
    uid      = str(uuid.uuid4())
    now_utc  = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    all_day  = bool(event.get("all_day", False))
    title    = _clean(event["title"])
    location = _clean(event.get("location", ""))
    notes    = _clean(event.get("notes", ""))
    url      = _clean(event.get("url", ""))
    status   = _clean(event.get("status", "CONFIRMED"))
    transp   = _clean(event.get("transparency", "OPAQUE"))
    cats     = event.get("categories") or []

    lines = [
        "BEGIN:VCALENDAR",         # Inicio del contenedor de calendario
        "VERSION:2.0",             # Versión del formato iCalendar
        "PRODID:Temas_IA iCloud Agent",  # Identificador del software que lo crea
        "BEGIN:VEVENT",            # Inicio del evento
        f"UID:{uid}",              # ID global único (para que iCloud no cree duplicados)
        f"DTSTAMP:{now_utc}",      # Timestamp de cuándo se creó este ICS
        f"SUMMARY:{title}",        # Título del evento
        f"STATUS:{status}",        # CONFIRMED / TENTATIVE / CANCELLED
        f"TRANSP:{transp}",        # OPAQUE (bloquea tiempo) / TRANSPARENT (no bloquea)
    ]

    if all_day:
        lines.append(f"DTSTART;VALUE=DATE:{_fmt_date(event['start'])}")
        lines.append(f"DTEND;VALUE=DATE:{_fmt_date(event['end'])}")
    else:
        lines.append(f"DTSTART:{_fmt_utc(event['start'])}")
        lines.append(f"DTEND:{_fmt_utc(event['end'])}")

    if location:
        lines.append(f"LOCATION:{location}")
    if notes:
        lines.append(f"DESCRIPTION:{notes}")
    if cats:
        lines.append(f"CATEGORIES:{','.join(_clean(c) for c in cats)}")
    if url:
        lines.append(f"URL:{url}")

    rrule = _build_rrule(event)   # Recurrencia (si la hay)
    if rrule:
        lines.append(rrule)

    lines.extend(_build_valarms(event))  # Alarmas/recordatorios
    lines.extend(["END:VEVENT", "END:VCALENDAR", ""])

    return "\r\n".join(lines)     # CRLF obligatorio por RFC 5545
```

**iCalendar (ICS, RFC 5545)** es el formato estándar universal para eventos de calendario. Lo entienden Apple Calendar, Google Calendar, Outlook, Thunderbird, etc. Es texto plano con una estructura de tipo "BEGIN/END":

```
BEGIN:VCALENDAR          ← Contenedor raíz
  BEGIN:VEVENT           ← Un evento
    SUMMARY:Médico       ← Título
    DTSTART:20260425T070000Z  ← Inicio (UTC)
    BEGIN:VALARM          ← Una alarma
      TRIGGER:-PT30M      ← 30 min antes
    END:VALARM
  END:VEVENT
END:VCALENDAR
```

**Por qué `uuid.uuid4()` para el UID:** Cada evento necesita un identificador globalmente único. Si dos eventos tienen el mismo UID, CalDAV los considera el mismo evento (y actualizaría en lugar de crear). UUID v4 genera un ID aleatorio de 128 bits — la probabilidad de colisión es astronómicamente baja.

**Por qué `\r\n` (CRLF):** RFC 5545 especifica que las líneas ICS deben terminar en `\r\n`. Muchos servidores CalDAV aceptan `\n` solo, pero otros (incluido iCloud a veces) lo rechazan. Usar CRLF es lo correcto y evita problemas.

### 10.4 Recurrencia (RRULE)

```python
def _build_rrule(event: dict) -> str:
    freq = event.get("repeat_freq")
    if not freq:
        return ""

    parts = [f"FREQ={freq}"]                        # FREQ=WEEKLY

    interval = event.get("repeat_interval", 1)
    if interval and interval != 1:
        parts.append(f"INTERVAL={interval}")         # INTERVAL=2 = cada 2 semanas

    if event.get("repeat_count"):
        parts.append(f"COUNT={event['repeat_count']}")  # COUNT=10 = 10 repeticiones

    if event.get("repeat_until"):
        parts.append(f"UNTIL={_fmt_utc(event['repeat_until'])}")  # Hasta fecha X

    if event.get("repeat_byday"):
        parts.append(f"BYDAY={','.join(event['repeat_byday'])}")  # BYDAY=MO,WE,FR

    return "RRULE:" + ";".join(parts)
    # Ejemplo: "RRULE:FREQ=WEEKLY;BYDAY=MO,WE,FR"
```

Ejemplos de frases del usuario → RRULE:

| Frase | RRULE |
|---|---|
| "todos los días" | `RRULE:FREQ=DAILY` |
| "cada lunes y miércoles" | `RRULE:FREQ=WEEKLY;BYDAY=MO,WE` |
| "cada 2 semanas" | `RRULE:FREQ=WEEKLY;INTERVAL=2` |
| "los primeros de cada mes, 6 veces" | `RRULE:FREQ=MONTHLY;COUNT=6` |
| "cada año hasta 2030" | `RRULE:FREQ=YEARLY;UNTIL=20301231T230000Z` |

### 10.5 Alarmas (VALARM)

```python
def _build_valarms(event: dict) -> list[str]:
    lines = []
    for alarm in (event.get("alarms") or []):
        lines.extend([
            "BEGIN:VALARM",
            f"ACTION:{_clean(alarm.get('action', 'DISPLAY'))}",
            f"DESCRIPTION:{_clean(alarm.get('description', 'Recordatorio'))}",
            f"TRIGGER:{_trigger(alarm['trigger_minutes_before'])}",
            "END:VALARM",
        ])
    return lines
```

**`ACTION:DISPLAY`:** Significa que la alarma muestra una notificación en pantalla. Otros valores posibles son `AUDIO` (suena) y `EMAIL` (envía un correo), pero `DISPLAY` es el único soportado universalmente por todos los clientes de calendario.

### 10.6 Conexión CalDAV

```python
def connect_client() -> caldav.DAVClient:
    if not ICLOUD_EMAIL or not ICLOUD_APP_PASSWORD:
        raise EnvironmentError("Faltan ICLOUD_EMAIL o ICLOUD_APP_PASSWORD en el .env")
    clean_pwd = ICLOUD_APP_PASSWORD.replace(" ", "").replace("-", "")
    return caldav.DAVClient(url=CALDAV_URL, username=ICLOUD_EMAIL, password=clean_pwd)
```

**Por qué `clean_pwd`:** Las App Passwords de Apple se muestran con guiones y espacios para legibilidad (ej: `abcd-efgh-ijkl-mnop`). Pero la API CalDAV espera el password sin separadores (`abcdefghijklmnop`). La limpieza evita que el usuario tenga que quitar los guiones manualmente.

**CalDAV (RFC 4791)** es un protocolo de calendario basado en HTTP. Es básicamente WebDAV (protocolo de archivos sobre HTTP) + extensiones para calendarios. La librería Python `caldav` abstrae las peticiones HTTP — no necesitas construir XML a mano.

### 10.7 Búsqueda del calendario

```python
def find_calendar(calendars, target_name: str):
    target = target_name.strip().lower()
    for cal in calendars:
        if _calendar_name(cal).strip().lower() == target:
            return cal
    return None
```

**Búsqueda case-insensitive:** El usuario puede configurar `ICLOUD_DEFAULT_CALENDAR="Cari y Cosi"` pero en iCloud el calendario se llama `"cari y cosi"` o `"CARI Y COSI"`. La comparación `.lower()` evita problemas.

**Si no se encuentra:** `create_event` lista los calendarios disponibles en el mensaje de error. Esto es deliberado — cuando algo falla, dale al usuario suficiente información para que pueda corregirlo.

### 10.8 Validación

```python
def validate_event(event: dict) -> None:
    for field in ("title", "start", "end"):
        if not event.get(field):
            raise ValueError(f"Campo obligatorio ausente: {field}")

    if not isinstance(event["start"], datetime):
        raise ValueError("start debe ser datetime")
    if not isinstance(event["end"], datetime):
        raise ValueError("end debe ser datetime")
    if event["end"] <= event["start"]:
        raise ValueError("end debe ser posterior a start")

    freq = event.get("repeat_freq")
    if freq and freq not in {"DAILY", "WEEKLY", "MONTHLY", "YEARLY"}:
        raise ValueError("repeat_freq inválido")

    status = event.get("status", "CONFIRMED")
    if status not in {"CONFIRMED", "TENTATIVE", "CANCELLED"}:
        raise ValueError("status debe ser CONFIRMED, TENTATIVE o CANCELLED")

    for alarm in (event.get("alarms") or []):
        if "trigger_minutes_before" not in alarm:
            raise ValueError("Cada alarma debe incluir trigger_minutes_before")
```

**Por qué validar aquí si Pydantic ya validó:** Pydantic valida la **estructura del JSON del LLM**. Esta función valida la **semántica del evento** después de la transformación. Ejemplo: Pydantic verifica que `start` es un `str`, pero no puede verificar que `end > start` (son strings en ese punto). Aquí, después de convertir a `datetime`, sí podemos hacer esa verificación.

**Principio: Validate at boundaries.** Cada vez que datos cruzan una frontera entre capas (IA → integración), se validan. Es mejor detectar un error aquí que dejarlo llegar a CalDAV donde el error sería un HTTP 400 críptico de Apple.

### 10.9 Punto de entrada: `create_event`

```python
def create_event(event: dict) -> str:
    validate_event(event)                    # 1. Validar el evento

    client     = connect_client()            # 2. Conectar a iCloud
    principal  = client.principal()           # 3. Obtener el "principal" (usuario)
    calendars  = list_calendars(principal)    # 4. Listar todos los calendarios

    cal_name   = event.get("calendar_name") or DEFAULT_CALENDAR_NAME
    calendar   = find_calendar(calendars, cal_name)  # 5. Buscar el calendario target

    if calendar is None:                     # 6. Error si no existe
        available = ", ".join(_calendar_name(c) for c in calendars)
        raise Exception(
            f"Calendario '{cal_name}' no encontrado. Disponibles: {available}"
        )

    ics_data     = build_ics(event)          # 7. Construir el ICS
    saved_event  = calendar.save_event(ics_data)  # 8. HTTP PUT a iCloud

    return str(saved_event.url)              # 9. Devolver la URL del evento creado
```

**¿Qué es `principal`?** En CalDAV, el "principal" es el usuario autenticado. De él cuelgan los calendarios. Es un concepto de WebDAV heredado — piensa en él como "tu cuenta".

**`calendar.save_event(ics_data)`** internamente hace un HTTP PUT a una URL como `https://caldav.icloud.com/{user}/calendars/{calendar_id}/{event_uid}.ics` con el contenido ICS. Si Apple acepta el evento, devuelve un HTTP 201 Created y la librería `caldav` lo envuelve en un objeto con `.url`.

---

## 11. La API REST: `api.py`

**Archivo:** `events/api.py`

### Autenticación por API Key

```python
_API_KEY = os.getenv("API_KEY", "")
_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def _require_api_key(key: str = Security(_api_key_header)) -> str:
    if not _API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API_KEY not configured on the server.",
        )
    if not key or not secrets.compare_digest(key, _API_KEY):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key.",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    return key
```

**Por qué API Key y no OAuth/JWT:** Para una API personal (un solo usuario, un solo cliente), una API Key es suficiente y mucho más simple. OAuth tiene sentido cuando tienes múltiples usuarios con permisos diferentes.

**Por qué `secrets.compare_digest` en lugar de `==`:**

```python
# INSEGURO:
if key == _API_KEY:  # ❌ Vulnerable a timing attacks

# SEGURO:
if secrets.compare_digest(key, _API_KEY):  # ✅ Constante en tiempo
```

Cuando Python compara strings con `==`, se detiene en el primer carácter diferente. Un atacante puede medir los microsegundos de respuesta para adivinar la key carácter a carácter (esto se llama **timing attack**). `secrets.compare_digest()` siempre tarda exactamente lo mismo independientemente de cuántos caracteres coincidan.

**Por qué `auto_error=False` en `APIKeyHeader`:** Con `auto_error=True` (default), FastAPI lanza automáticamente un 403 si no viene el header. Con `False`, le damos el control a nuestra función `_require_api_key` para lanzar un 401 con un mensaje customizado. El 401 es semánticamente más correcto que el 403 (401 = "no autenticado", 403 = "autenticado pero sin permiso").

**Por qué check `if not _API_KEY`:** Si el servidor arranca sin la variable `API_KEY` configurada, devolvemos 500 en lugar de aceptar cualquier petición. Es una protección contra despliegues olvidando la configuración.

### Configuración de la app FastAPI

```python
app = FastAPI(
    title="Calendar Event API",
    version="1.0.0",
    docs_url=None,    # Deshabilitamos Swagger UI
    redoc_url=None,   # Deshabilitamos ReDoc
)
```

**Por qué deshabilitamos la documentación:** En producción, la documentación auto-generada de FastAPI (`/docs`, `/redoc`) expone todos los endpoints, sus parámetros y formatos. Para una API pública esto es útil, pero para una API personal es superficie de ataque innecesaria.

### Esquemas de request/response

```python
class EventRequest(BaseModel):
    message: str  # "Cita con el médico el viernes a las 10"


class EventResponse(BaseModel):
    ok: bool
    event: dict
```

**Por qué modelos Pydantic para request/response:** FastAPI usa estos modelos para:
1. **Validar la entrada:** Si alguien envía un POST sin `message`, FastAPI devuelve un 422 automáticamente.
2. **Serializar la salida:** FastAPI convierte el objeto `EventResponse` a JSON automáticamente.
3. **Documentación:** Si habilitaras `/docs`, estos modelos aparecerían documentados.

### Endpoint `/health`

```python
@app.get("/health", status_code=status.HTTP_200_OK)
def health():
    return {"status": "ok"}
```

**Para qué sirve:** Render envía peticiones periódicas a este endpoint para verificar que el servidor está vivo (`healthCheckPath: /health` en `render.yaml`). Si no responde, Render reinicia el servicio. No requiere autenticación porque Render no envía API keys.

### Endpoint `/ping`

```python
@app.post("/ping", status_code=status.HTTP_200_OK)
def ping():
    return {"status": "ok"}
```

**Para qué sirve:** Los servicios gratuitos de Render se "duermen" tras 15 minutos de inactividad. Cuando llega una petición a un servicio dormido, tarda ~30 segundos en "despertar" (cold start). Si usas este sistema desde un Shortcut de iPhone, esos 30 segundos son muy molestos.

**La solución:** Antes de crear un evento, el Shortcut envía un POST a `/ping` para despertar el servidor. Mientras el usuario escribe el texto del evento, el servidor ya está listo. Es POST en lugar de GET por compatibilidad con Shortcuts de iOS (que maneja mejor las peticiones POST).

### Endpoint `/event` — El principal

```python
@app.post("/event", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
def create_calendar_event(
    body: EventRequest,
    dry_run: bool = Query(False, description="Si es true, extrae pero NO crea."),
    _: str = Depends(_require_api_key),
):
```

**`Depends(_require_api_key)`:** Inyección de dependencias de FastAPI. Antes de ejecutar la función, FastAPI llama a `_require_api_key`. Si lanza HTTPException, la función del endpoint ni se ejecuta. El `_` indica que no usamos el valor de retorno — solo nos importa que no lance error.

**`dry_run: bool = Query(False)`:** Parámetro de query string. `POST /event?dry_run=true` ejecuta toda la cadena IA pero NO crea el evento en iCloud. El resultado se devuelve en la respuesta JSON y se loguea en el servidor. Esto permite:
- Verificar qué va a crear el LLM antes de crearlo.
- Depurar problemas de extracción sin generar eventos basura.
- Testear la API end-to-end sin credenciales de iCloud.

#### Flujo interno del endpoint

```python
    # PASO 1: Invocar la cadena de IA
    try:
        extracted = _get_chain().invoke({"user_message": body.message})
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Error al extraer el evento: {exc}",
        ) from exc
```

Llama a la cadena LCEL completa (prompt → LLM → json_cleaner → parser). Si el LLM devuelve algo no parseable, el error se captura y se devuelve un 422 con detalle del fallo.

**Por qué 422 y no 400:** 422 = "Unprocessable Entity" — el servidor entiende la petición (el JSON es válido, tiene `message`) pero no puede procesarla (el LLM no logró extraer un evento). 400 = "Bad Request" — la petición en sí es malformada.

```python
    # PASO 2: Construir el dict del evento
    try:
        event_dict = build_event_dict(extracted)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Error al construir el evento: {exc}",
        ) from exc
```

Convierte `EventExtraction` → dict con datetimes. Podría fallar si `_parse_dt` no puede parsear la fecha que devolvió el LLM.

```python
    # PASO 3: Preview en logs (siempre)
    logger.info(
        "[PREVIEW] Evento a crear:\n"
        "  Título      : %s\n"
        "  Inicio      : %s\n"
        "  Fin         : %s\n"
        "  Lugar       : %s\n"
        ...
        "  dry_run     : %s",
        event_dict.get("title"),
        event_dict.get("start"),
        ...
        dry_run,
    )
```

El preview se loguea SIEMPRE (sea `dry_run` o no). Esto te da visibilidad en los logs de Render de cada evento que se crea (o intenta crear). Si un evento se crea mal, puedes revisar los logs y ver exactamente qué datos tenía.

```python
    # PASO 4: Crear en iCloud (solo si no es dry_run)
    if not dry_run:
        try:
            create_event(event_dict)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Error al crear el evento en iCloud: {exc}",
            ) from exc
```

**Por qué 502:** 502 = "Bad Gateway" — el servidor (nuestro API) actuó como proxy hacia otro servicio (iCloud CalDAV) y ese servicio falló. Es semánticamente correcto: el fallo no es de nuestra API sino de la conexión con iCloud.

```python
    # PASO 5: Respuesta
    summary = {
        "title": event_dict["title"],
        "start": event_dict["start"].isoformat(),   # datetime → str para JSON
        "end": event_dict["end"].isoformat(),
        "location": event_dict.get("location") or None,
        "notes": event_dict.get("notes") or None,
        "all_day": event_dict.get("all_day", False),
        "alarms": [
            {"minutes_before": a["trigger_minutes_before"]}
            for a in event_dict.get("alarms", [])
        ],
        "calendar": event_dict.get("calendar_name") or None,
    }

    return EventResponse(ok=True, event=summary)
```

El `summary` convierte los datetimes a strings ISO (porque JSON no tiene tipo datetime). También simplifica los alarms a solo `minutes_before` — el cliente no necesita saber el `action` ni el `description` internos.

---

## 12. Despliegue en Render

**Archivo:** `render.yaml` (en la raíz)

```yaml
services:
  - type: web
    name: temas-ia-events
    runtime: python
    buildCommand: pip install uv && uv sync
    startCommand: uv run uvicorn events.api:app --host 0.0.0.0 --port $PORT
    healthCheckPath: /health
    envVars:
      - key: PYTHON_VERSION
        value: "3.11.0"
      - key: LLM_PROVIDER
        value: openai
      - key: LLM_MODEL
        value: gpt-4o-mini
      - key: LLM_TEMPERATURE
        value: "0"
      - key: EMBEDDING_PROVIDER
        value: openai
      - key: EMBEDDING_MODEL
        value: text-embedding-3-small
      # Secretos — se rellenan en el Dashboard de Render, NO aquí
      - key: OPENAI_API_KEY
        sync: false
      - key: API_KEY
        sync: false
      - key: ICLOUD_EMAIL
        sync: false
      - key: ICLOUD_APP_PASSWORD
        sync: false
      - key: ICLOUD_DEFAULT_CALENDAR
        sync: false
```

### Cómo funciona el despliegue

**Render auto-despliega automáticamente.** No necesitamos GitHub Actions, CI/CD, ni ningún pipeline. Cuando conectas tu repo de GitHub a Render:

1. Cada `git push` al branch conectado (normalmente `main`) dispara un nuevo despliegue automáticamente.
2. Render ejecuta `buildCommand` (`pip install uv && uv sync`) — instala `uv` y luego instala todas las dependencias del proyecto.
3. Render ejecuta `startCommand` (`uv run uvicorn events.api:app --host 0.0.0.0 --port $PORT`) — arranca el servidor.
4. Render comprueba `healthCheckPath` (`/health`) — si responde 200, el despliegue es exitoso.

### Por qué `sync: false` en los secretos

```yaml
- key: OPENAI_API_KEY
  sync: false
```

`sync: false` significa: "este valor se configura manualmente en el dashboard de Render, NO en este archivo YAML". Los secretos (API keys, passwords) nunca deben estar en código — ni en el YAML, ni en un `.env` que se commitee. Render los almacena cifrados en su plataforma.

### Por qué `uv` y no `pip`

`uv` es un instalador de paquetes Python escrito en Rust. Es 10-100x más rápido que `pip`. En Render, donde el build tiene un timeout, usar `uv` reduce significativamente el tiempo de despliegue. La configuración de dependencias está en `pyproject.toml`.

---

## 13. Conceptos clave reutilizables

Estos son los patrones que puedes aplicar a cualquier otro proyecto de IA, no solo a este:

### Structured Output con Pydantic

```
Pydantic Model  →  format_instructions  →  Prompt  →  LLM  →  JSON  →  Pydantic Model
       ↑                                                                        ↑
  Define el esquema                                                  Valida la respuesta
```

Úsalo siempre que necesites extraer datos estructurados de texto libre: facturas, CVs, tickets de soporte, correos, formularios, etc. Es el patrón más importante de aplicaciones LLM en producción.

### LCEL (LangChain Expression Language)

```python
chain = prompt | llm | output_cleaner | parser
```

Componer runnables con `|` tiene tres ventajas:
1. **Legibilidad:** Ves todo el flujo de datos en una línea.
2. **Debugging:** Puedes insertar `debug_step` entre cualquier par de componentes.
3. **Modularidad:** Puedes sustituir un componente (otro LLM, otro parser) sin reescribir la cadena.

### Separación IA / Integración

La capa IA produce un objeto Python tipado. La capa de integración lo consume. **Nunca** mezcles lógica de LLM con llamadas a APIs externas en la misma función. Si lo haces:
- No puedes testear la IA sin tener credenciales de la API externa.
- No puedes reusar la integración con otra fuente de datos.
- Los errores son ambiguos (¿falló el LLM o la API?).

### Temperature 0 para extracción

Para cualquier tarea donde la respuesta es objetiva (extraer datos, clasificar, transformar formato), usa `temperature=0`. Para tareas creativas (escribir textos, brainstorming), usa `temperature=0.7-1.0`.

### Dry run antes de actuar

Para cualquier acción irreversible (crear, borrar, enviar), implementa un modo de previsualización. Es una línea de código (`if not dry_run:`) que ahorra horas de debugging y eventos fantasma.

### Variables de entorno para todo lo configurable

Proveedores LLM, modelos, calendarios por defecto, API keys... todo en `.env` / variables de entorno. El código nunca tiene valores hardcodeados que cambien entre entornos (local vs producción). Esto se llama **12-factor app** (concretamente, el factor III: Config).

### Validar en las fronteras

Cada vez que datos cruzan de una capa a otra, valídalos:
- LLM → JSON string: `json.loads()` + regex fallback en `extract_json_text`
- JSON → Pydantic: `PydanticOutputParser` valida tipos y campos
- Pydantic → dict: `build_event_dict` transforma tipos (str → datetime)
- dict → iCloud: `validate_event` verifica semántica (end > start, etc.)

Cada validación detecta errores lo más cerca posible de donde se originan, produciendo mensajes de error útiles en lugar de stacktraces incomprensibles.
