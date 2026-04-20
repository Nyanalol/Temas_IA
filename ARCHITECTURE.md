# Arquitectura del proyecto

## Visión general

```mermaid
graph TD
    CFG["⚙️ config.py\nProveedor LLM / Embeddings\n.env"]

    subgraph AGENTS["📦 agents/"]
        AM["main.py\nEntry point"]
        ACF["chain_factory.py\nConstruye la cadena LCEL"]
        AP["prompts.py"]
        APA["parsers.py"]
        AR["runnables.py\nTransformaciones y debug"]
        AMO["models.py\nIncidentExtraction\nIncidentResponse"]
    end

    subgraph RAG["📦 rag/"]
        RM["pipeline.py\nEntry point"]
        RC["connectors/\ntxt · pdf · csv · json · md · docx"]
        RLP["local_persist.py\nChromaDB en disco"]
        ROM["override_metadata.py"]
        RI["inputs/\nDocumentos fuente"]
    end

    subgraph EMB["📦 embeddings/"]
        EE["embeddings.py\nExploratorio\nDeBERTa · SentenceTransformers"]
    end

    subgraph WIP["🚧 En desarrollo"]
        WLG["_wip_langgraph/"]
        WME["_wip_memory/"]
        WTO["_wip_tools/"]
        WPE["_wip_prompt_engineering/"]
        WRA["_wip_rag_advanced/"]
        WFT["_wip_fine_tuning/"]
        WEV["_wip_evaluation/"]
    end

    CFG --> ACF
    CFG --> RM

    AM --> ACF
    ACF --> AP
    ACF --> APA
    ACF --> AR
    APA --> AMO
    AR --> AMO

    RM --> RC
    RM --> RLP
    RM --> ROM
    RC --> RI

    WLG -.->|"usará"| CFG
    WTO -.->|"extenderá"| AGENTS
    WRA -.->|"extenderá"| RAG
```

---

## Flujo del agente LCEL (`agents/`)

```mermaid
sequenceDiagram
    participant U as Usuario
    participant M as main.py
    participant CF as chain_factory
    participant LLM as LLM (Ollama/OpenAI/...)
    participant P1 as extraction_parser
    participant R as custom_runnable
    participant P2 as response_parser

    U->>M: USER_MESSAGE
    M->>CF: build_incident_chain()
    M->>LLM: chain.invoke(user_message)
    LLM-->>P1: JSON con campos del incidente
    P1-->>R: IncidentExtraction (Pydantic)
    R-->>LLM: incident_context + format_instructions
    LLM-->>P2: JSON con respuesta operacional
    P2-->>M: IncidentResponse (Pydantic)
    M->>U: incident_summary, business_impact, next_action, owner_team
```

---

## Flujo del pipeline RAG (`rag/`)

```mermaid
flowchart LR
    I["📁 inputs/\ntxt · pdf · csv\njson · md · docx"]
    C["connectors/\nload_all()"]
    M["override_metadata()"]
    V["ChromaDB\nlocal_persist.py"]
    Q["Query del usuario"]
    S["similarity_search(k=5)"]
    L["LLM\nconfig.py"]
    R["Respuesta"]

    I --> C --> M --> V
    Q --> S
    V --> S --> L --> R
```

---

## Configuración por entorno (`.env`)

```mermaid
graph LR
    ENV[".env"]
    ENV -->|LLM_PROVIDER| CFG["config.py"]
    ENV -->|LLM_MODEL| CFG
    ENV -->|LLM_TEMPERATURE| CFG
    ENV -->|EMBEDDING_PROVIDER| CFG
    ENV -->|EMBEDDING_MODEL| CFG
    CFG -->|get_llm()| AGENTS["agents/"]
    CFG -->|get_llm() + get_embeddings()| RAG["rag/"]
```

---

## Estructura de carpetas

```
temas_ia/
├── config.py                  # Configuración central de LLM y embeddings
├── pyproject.toml             # Paquete instalable (uv / pip install -e .)
│
├── agents/                    # Agente LCEL de análisis de incidentes
│   ├── __init__.py
│   ├── main.py                # Entry point  →  python -m agents.main
│   ├── models.py              # Pydantic: IncidentExtraction, IncidentResponse
│   ├── prompts.py             # ChatPromptTemplates
│   ├── parsers.py             # PydanticOutputParsers
│   ├── runnables.py           # Transformaciones y pasos de debug
│   └── chain_factory.py      # Ensambla la cadena LCEL completa
│
├── rag/                       # Pipeline RAG con ChromaDB
│   ├── __init__.py
│   ├── pipeline.py            # Entry point  →  python -m rag.pipeline
│   ├── local_persist.py       # Carga / crea vectorstore en disco
│   ├── override_metadata.py   # Etiquetado manual de documentos
│   ├── connectors/            # Un conector por formato (txt, pdf, csv...)
│   └── inputs/                # Documentos fuente organizados por formato
│
├── embeddings/
│   └── embeddings.py          # Exploratorio: DeBERTa + SentenceTransformers
│
└── _wip_*/                    # Notas y temario de temas en preparación
    ├── _wip_langgraph/        # Grafos de estado, ReAct, memoria, HITL
    ├── _wip_tools/            # Tool binding y agentes con herramientas
    ├── _wip_rag_advanced/     # RAG avanzado (reranking, HyDE, etc.)
    ├── _wip_memory/           # Memoria conversacional
    ├── _wip_prompt_engineering/
    ├── _wip_fine_tuning/
    └── _wip_evaluation/
```
