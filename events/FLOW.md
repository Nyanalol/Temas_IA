# Flujo completo del agente de calendario iCloud

> **Para quién es esto:** Un Data Engineer que conoce Python y quiere entender no solo "qué hace el código" sino **por qué está estructurado así** y qué conceptos de IA/LangChain aplica en cada paso. Al terminar de leer deberías poder replicar este patrón para cualquier otra tarea de extracción de información con LLMs.

---

## Índice

1. [Visión general del sistema](#1-visión-general-del-sistema)
2. [Punto de entrada: `main.py` (consola) y `api.py` (iPhone)](#2-punto-de-entrada)
3. [La cadena LangChain: `chain_factory.py`](#3-la-cadena-langchain-chain_factorypy)
4. [El modelo de datos: `models.py`](#4-el-modelo-de-datos-modelspy)
5. [El prompt: `prompts.py`](#5-el-prompt-promptspy)
6. [El LLM: `config.py`](#6-el-llm-configpy)
7. [La limpieza del JSON: `runnables.py` → `extract_json_text`](#7-la-limpieza-del-json)
8. [El parser: `parsers.py`](#8-el-parser-parserspy)
9. [Convertir el modelo a diccionario: `runnables.py` → `build_event_dict`](#9-convertir-el-modelo-a-diccionario)
10. [La integración con iCloud: `icloud.py`](#10-la-integración-con-icloud-icloudpy)
11. [La API REST: `api.py`](#11-la-api-rest-apipy)
12. [Conceptos clave reutilizables](#12-conceptos-clave-reutilizables)

---

## 1. Visión general del sistema

El sistema convierte lenguaje natural en un evento de calendario de Apple iCloud. La arquitectura tiene dos capas bien diferenciadas:

```
Usuario (texto libre)
        │
        ▼
┌───────────────────────┐
│   CAPA IA (LangChain) │   Prompt → LLM → JSON → Pydantic
│  chain_factory.py     │
└───────────┬───────────┘
            │  EventExtraction (objeto Python tipado)
            ▼
┌───────────────────────┐
│  CAPA INTEGRACIÓN     │   iCalendar (ICS) → CalDAV → iCloud
│  icloud.py            │
└───────────────────────┘
```

**Por qué esta separación es importante:** La capa de IA no sabe nada de iCloud, y la capa de integración no sabe nada de LLMs. Si mañana quieres crear eventos en Google Calendar, solo cambias `icloud.py`. Si cambias el LLM, solo tocas `config.py`. Este principio se llama **separación de responsabilidades** y es crítico para mantener el código.

---

## 2. Punto de entrada

Hay dos formas de arrancar el sistema:

### Modo consola (`events/main.py`)

```bash
python -m events.main
```

Este modo está pensado para desarrollo y pruebas locales. El flujo interactivo es:

1. Comprueba si Ollama está corriendo (`_ensure_ollama_running`). Si no, lo arranca.
2. Construye la cadena LangChain llamando a `build_event_chain()` (ver sección 3).
3. Entra en un bucle `while True` que:
   - Pide input al usuario (`input("Tú: ")`)
   - Invoca la cadena con `chain.invoke({"user_message": user_input})`
   - Muestra un **preview** del evento extraído (`_show_event_summary`)
   - Pide confirmación antes de crear nada en iCloud
   - Si el usuario confirma, llama a `create_event(event_dict)`

> **Concepto clave:** La confirmación manual antes de crear el evento es una buena práctica con LLMs. Los modelos pueden alucinar fechas o datos. Nunca hagas acciones irreversibles (crear, borrar, enviar) sin una validación humana o al menos un paso de revisión.

### Modo API (`events/api.py`)

```bash
uvicorn events.api:app --host 0.0.0.0 --port 8000
```

Es una API FastAPI con tres endpoints:

| Endpoint | Método | Auth | Descripción |
|---|---|---|---|
| `/health` | GET | No | Comprueba que el servidor responde |
| `/ping` | POST | No | Wake-up del servidor sin crear eventos |
| `/event` | POST | Sí (X-API-Key) | Crea un evento en iCloud |

El endpoint `/event` acepta un parámetro de query `?dry_run=true` que ejecuta toda la cadena IA y loguea el resultado, pero **no llama a iCloud**. Útil para verificar qué va a crear antes de hacerlo.

> **Por qué FastAPI y no Flask:** FastAPI genera validación automática con Pydantic, documentación OpenAPI y es asíncrono por naturaleza. Perfecto para APIs que envuelven llamadas lentas a LLMs.

---

## 3. La cadena LangChain (`chain_factory.py`)

**Archivo:** `events/chain_factory.py`

```python
chain = (
    debug_step("INPUT")
    | prompt
    | debug_step("PROMPT")
    | llm
    | json_cleaner
    | debug_step("JSON_CLEAN")
    | parser
    | debug_step("EXTRACTED_EVENT")
)
```

Este es el núcleo del sistema. Es una **LangChain Expression Language (LCEL) chain**, que funciona como un pipeline Unix (`|`): la salida de cada paso es la entrada del siguiente.

Cada componente de la cadena:

| Paso | Tipo | Entrada | Salida |
|---|---|---|---|
| `debug_step("INPUT")` | `RunnableLambda` | `dict` con `user_message` | mismo `dict` (pass-through) |
| `prompt` | `ChatPromptTemplate` | `dict` | `ChatPromptValue` (los mensajes formateados) |
| `llm` | `ChatOllama` / `ChatOpenAI` / etc. | `ChatPromptValue` | `AIMessage` con el texto del LLM |
| `json_cleaner` | `RunnableLambda` | `AIMessage` | `str` con JSON limpio |
| `parser` | `PydanticOutputParser` | `str` JSON | `EventExtraction` (objeto Pydantic) |

> **Concepto clave — LCEL:** El operador `|` en LangChain no es un OR lógico, es **composición de Runnables**. Cualquier objeto que implemente la interfaz `Runnable` (con método `.invoke()`) puede componerse así. Esto incluye prompts, LLMs, parsers, funciones Python envueltas en `RunnableLambda`, o incluso otras chains. Es el patrón más importante de LangChain moderno.

> **Concepto clave — lazy init:** La cadena se construye una sola vez la primera vez que llega un request (`_chain = None` → `_get_chain()`). Construir la cadena carga el modelo en memoria. Hacerlo en el arranque del servidor alarga el cold start innecesariamente.

---

## 4. El modelo de datos (`models.py`)

**Archivo:** `events/models.py`

```python
class EventExtraction(BaseModel):
    title: str
    start: str  # ISO 8601
    end: str    # ISO 8601
    location: Optional[str] = None
    alarms: Optional[list[AlarmInput]] = None
    calendar_name: Optional[str] = None
    # ... más campos
```

Este modelo Pydantic cumple **dos roles al mismo tiempo:**

1. **Esquema de salida del LLM:** `PydanticOutputParser` lee los campos y sus `Field(description=...)` para generar automáticamente las instrucciones de formato que se inyectan en el prompt (ver sección 5). El LLM "sabe" qué campos debe rellenar porque el parser los describe.

2. **Validación de la respuesta:** Cuando el LLM devuelve el JSON, Pydantic verifica que los tipos sean correctos, que los campos obligatorios estén presentes, etc. Si el LLM alucina y devuelve un formato incorrecto, Pydantic lanza una excepción en lugar de propagar datos corruptos.

> **Concepto clave — Structured Output:** Este patrón (LLM + Pydantic model) es la forma estándar de extraer información estructurada con LLMs. Se llama **structured output** o **information extraction**. En lugar de pedirle al LLM que "devuelva JSON", le das un esquema exacto con descripciones de cada campo. El LLM entiende las descripciones (son lenguaje natural) y las usa para decidir qué poner en cada campo. Es mucho más fiable que parsear texto libre.

---

## 5. El prompt (`prompts.py`)

**Archivo:** `events/prompts.py`

```python
_DEFAULT_CALENDAR = os.getenv("ICLOUD_DEFAULT_CALENDAR", "Cari y Cosi")

def get_extract_prompt(format_instructions: str) -> ChatPromptTemplate:
    today = date.today().isoformat()
    return ChatPromptTemplate.from_messages([
        ("system", "You are a calendar assistant. ...\n"
                   f"Today's date is {today}.\n"
                   f"The default calendar is '{_DEFAULT_CALENDAR}'.\n"
                   "Rules: ..."),
        ("human", "{user_message}\n\n{format_instructions}"),
    ]).partial(format_instructions=format_instructions)
```

El prompt tiene dos partes:

- **System message:** Define el rol del LLM, le da contexto de fecha (imprescindible para resolver "mañana", "el martes") y reglas de negocio (duración por defecto, calendario por defecto, etc.).
- **Human message:** El mensaje real del usuario más las instrucciones de formato generadas por el parser.

El método `.partial(format_instructions=...)` pre-rellena una variable del template para que cuando la cadena invoque el prompt solo tenga que pasar `user_message`. Es como `functools.partial` pero para prompts.

> **Concepto clave — Prompt Engineering:**  
> - Siempre inyecta la **fecha actual** cuando el LLM necesita resolver fechas relativas. Sin esto, el LLM inventará fechas o usará las de su entrenamiento.  
> - Las **reglas explícitas** en el system message ("si no especifica duración, pon 1 hora") son más fiables que esperar que el LLM lo infiera.  
> - Las **instrucciones de formato** al final del human message funcionan mejor que en el system message porque el LLM les presta más atención en esa posición.

---

## 6. El LLM (`config.py`)

**Archivo:** `config.py`

```python
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")  # ollama | openai | anthropic | groq
LLM_MODEL    = os.getenv("LLM_MODEL",    "llama3")

def get_llm():
    if LLM_PROVIDER == "ollama":
        return ChatOllama(model=LLM_MODEL, temperature=LLM_TEMPERATURE)
    if LLM_PROVIDER == "openai":
        return ChatOpenAI(model=LLM_MODEL, ...)
    # ...
```

El LLM es intercambiable vía `.env`. No hay referencias directas al proveedor en ningún otro archivo.

> **Concepto clave — Temperature:**  
> Para tareas de extracción de información estructurada, usa **`temperature=0`**. Temperature controla la aleatoriedad de la respuesta. Con temperature 0, el modelo es determinista y elige siempre el token más probable, lo que reduce alucinaciones en tareas donde la respuesta correcta es objetiva. Con temperature alta (>0.7), el modelo es más "creativo", útil para generación de texto pero peligroso para extracción.

> **Concepto clave — Abstracción de proveedores LangChain:**  
> `ChatOllama`, `ChatOpenAI`, `ChatAnthropic` y `ChatGroq` todos implementan la misma interfaz `BaseChatModel`. Eso significa que la cadena (`prompt | llm | parser`) funciona igual independientemente del proveedor. LangChain actúa como una capa de abstracción sobre las APIs de los distintos LLMs.

---

## 7. La limpieza del JSON

**Archivo:** `events/runnables.py` → función `extract_json_text`

```python
def extract_json_text(model_output) -> str:
    text = model_output.content  # AIMessage → str
    try:
        json.loads(text)  # Intento 1: el texto ya es JSON válido
        return text
    except Exception:
        pass
    match = re.search(r"\{.*\}", text, re.DOTALL)  # Intento 2: extraer JSON de markdown
    if match:
        json.loads(match.group(0))  # Verificar que es JSON válido
        return match.group(0)
    raise ValueError(f"No valid JSON found:\n{text}")
```

Este paso existe porque **los LLMs no siempre devuelven JSON puro**. Aunque el prompt diga "devuelve solo JSON", muchos modelos añaden texto como:

```
Aquí está el JSON del evento:
```json
{"title": "Médico", ...}
```
```

El `json_cleaner` extrae el bloque JSON con regex antes de pasárselo al parser.

> **Concepto clave — Robustez frente a LLMs:**  
> Nunca asumas que un LLM sigue las instrucciones al 100%. Añade capas de tolerancia: limpieza de salida, reintentos, validación con Pydantic. Los modelos más potentes (GPT-4, Claude 3) suelen devolver JSON limpio, pero los modelos locales (Llama, Mistral) son más inconsistentes.

---

## 8. El parser (`parsers.py`)

**Archivo:** `events/parsers.py`

```python
def get_event_parser() -> PydanticOutputParser:
    return PydanticOutputParser(pydantic_object=EventExtraction)
```

`PydanticOutputParser` hace dos cosas:

1. **`parser.get_format_instructions()`** → genera texto como "Return a JSON object with the following fields: title (str), start (str ISO 8601), ..." que se inyecta en el prompt.
2. **`parser.invoke(json_str)`** → parsea el JSON a un objeto `EventExtraction`.

> **Concepto clave — Output Parsers:**  
> LangChain tiene varios parsers: `StrOutputParser` (texto plano), `JsonOutputParser` (dict Python), `PydanticOutputParser` (objeto tipado), `CommaSeparatedListOutputParser`, etc. El de Pydantic es el más robusto para extracción de datos porque combina parsing con validación de tipos en un solo paso.

---

## 9. Convertir el modelo a diccionario

**Archivo:** `events/runnables.py` → función `build_event_dict`

```python
_DEFAULT_CALENDAR = os.getenv("ICLOUD_DEFAULT_CALENDAR", "Cari y Cosi")

def build_event_dict(extracted: EventExtraction) -> dict:
    event = {
        "title":  extracted.title,
        "start":  _parse_dt(extracted.start),   # str ISO → datetime con timezone
        "end":    _parse_dt(extracted.end),
        "calendar_name": extracted.calendar_name or _DEFAULT_CALENDAR,
        # ... resto de campos
    }
    return event
```

Este paso convierte el objeto Pydantic en un diccionario Python plano con tipos nativos (`datetime` en lugar de `str`). Actúa como **capa de transformación entre la capa IA y la capa de integración**.

La función `_parse_dt` añade timezone de Madrid si el LLM no la incluyó:

```python
def _parse_dt(iso_str: str) -> datetime:
    dt = datetime.fromisoformat(iso_str)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=ZoneInfo("Europe/Madrid"))
    return dt
```

> **Concepto clave — Timezones:**  
> Los LLMs devuelven fechas en ISO 8601 sin timezone (`2026-04-25T10:00:00`). iCloud trabaja en UTC. Siempre añade timezone local antes de convertir a UTC para que el evento aparezca a la hora correcta. Usa `zoneinfo` (Python 3.9+) en lugar del deprecado `pytz`.

---

## 10. La integración con iCloud (`icloud.py`)

**Archivo:** `events/icloud.py`

Este archivo no tiene nada de IA. Es integración pura con el protocolo CalDAV. El flujo es:

### 10.1 Autenticación CalDAV

```python
def connect_client() -> caldav.DAVClient:
    clean_pwd = ICLOUD_APP_PASSWORD.replace(" ", "").replace("-", "")
    return caldav.DAVClient(url="https://caldav.icloud.com",
                            username=ICLOUD_EMAIL,
                            password=clean_pwd)
```

Apple iCloud usa **CalDAV** (RFC 4791), un estándar abierto para calendarios sobre HTTP. La librería `caldav` implementa el protocolo. La contraseña debe ser una **App Password** de Apple (no tu contraseña normal), generada en [appleid.apple.com](https://appleid.apple.com) → Seguridad → Contraseñas de apps.

### 10.2 Búsqueda del calendario

```python
def find_calendar(calendars, target_name: str):
    target = target_name.strip().lower()
    for cal in calendars:
        if _calendar_name(cal).strip().lower() == target:
            return cal
    return None
```

Se busca el calendario por nombre (case-insensitive). Si no existe, se lanza una excepción con los nombres disponibles para que el usuario sepa cuál poner.

### 10.3 Construcción del ICS

```python
def build_ics(event: dict) -> str:
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "BEGIN:VEVENT",
        f"UID:{uuid.uuid4()}",
        f"SUMMARY:{event['title']}",
        f"DTSTART:{_fmt_utc(event['start'])}",
        # ...
        "END:VEVENT",
        "END:VCALENDAR",
    ]
    return "\r\n".join(lines)
```

**iCalendar (ICS)** es el formato estándar para eventos de calendario (RFC 5545). Es texto plano con una sintaxis específica. Puntos importantes:

- `UID`: identificador único del evento. Se genera con `uuid.uuid4()` para que sea globalmente único.
- `DTSTART` / `DTEND`: fechas en UTC con formato `YYYYMMDDTHHMMSSz`.
- Para eventos de todo el día: `DTSTART;VALUE=DATE:YYYYMMDD` (sin hora, sin Z).
- `RRULE`: recurrencia. Ejemplo: `RRULE:FREQ=WEEKLY;BYDAY=MO,WE,FR`.
- `VALARM`: recordatorio. El `TRIGGER` usa duración negativa: `-PT30M` = 30 min antes.
- El separador de línea **debe ser `\r\n`** (CRLF), no solo `\n`. Muchos clientes rechazan ICS con solo LF.

### 10.4 Subida a iCloud

```python
saved_event = calendar.save_event(ics_data)
return str(saved_event.url)
```

La librería `caldav` hace una petición HTTP PUT al servidor de Apple con el ICS. Si tiene éxito, devuelve la URL del evento creado.

---

## 11. La API REST (`api.py`)

**Archivo:** `events/api.py`

### Autenticación

```python
_API_KEY = os.getenv("API_KEY", "")

def _require_api_key(key: str = Security(_api_key_header)) -> str:
    if not secrets.compare_digest(key, _API_KEY):
        raise HTTPException(status_code=401, ...)
```

Se usa `secrets.compare_digest` en lugar de `==` para comparar la API key. Esto evita **timing attacks**: con `==`, un atacante puede medir el tiempo de respuesta para adivinar la key byte a byte. `compare_digest` siempre tarda el mismo tiempo independientemente de cuántos caracteres coincidan.

### El endpoint principal

```python
@app.post("/event")
def create_calendar_event(
    body: EventRequest,
    dry_run: bool = Query(False),
    _: str = Depends(_require_api_key),
):
    extracted = _get_chain().invoke({"user_message": body.message})
    event_dict = build_event_dict(extracted)

    logger.info("[PREVIEW] Evento a crear: título=%s, inicio=%s ...", ...)

    if not dry_run:
        create_event(event_dict)

    return EventResponse(ok=True, event=summary)
```

El parámetro `dry_run=True` permite ver en la respuesta JSON exactamente qué evento va a crear el LLM, sin crearlo. El preview también se loguea siempre en el servidor (visible en los logs de Render).

---

## 12. Conceptos clave reutilizables

Estos son los patrones que puedes aplicar a cualquier otro proyecto de IA, no solo a este:

### Structured Output con Pydantic

```
Pydantic Model → format_instructions → Prompt → LLM → JSON → Pydantic Model
```
Úsalo siempre que necesites extraer datos estructurados de texto libre: facturas, CVs, tickets de soporte, correos, etc.

### LCEL (LangChain Expression Language)

```python
chain = prompt | llm | output_cleaner | parser
```
Componer runnables con `|` hace el código legible, facilita el debugging (puedes insertar `debug_step` en cualquier punto) y permite sustituir componentes sin reescribir la cadena.

### Separación IA / Integración

La capa IA produce un objeto Python tipado. La capa de integración lo consume. Nunca mezcles lógica de LLM con llamadas a APIs externas en la misma función.

### Temperature 0 para extracción

Para cualquier tarea donde la respuesta es objetiva (extraer datos, clasificar, transformar formato), usa `temperature=0`.

### Dry run antes de actuar

Para cualquier acción irreversible (crear, borrar, enviar), implementa un modo de previsualización. Es barato de implementar y evita muchos errores en producción.

### Variables de entorno para todo lo configurable

Proveedores LLM, modelos, calendarios por defecto, API keys... todo en `.env`. El código nunca tiene valores hardcodeados que cambien entre entornos.
