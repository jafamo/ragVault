# RAG Chatbot — Plan de Proyecto

> **Chatbot de búsqueda documental con LangChain, modelos locales y aplicación web**

---

## 1. Visión General

Sistema RAG (Retrieval-Augmented Generation) que permite cargar documentos en múltiples formatos, indexarlos semánticamente y realizar consultas, resúmenes y preguntas-respuestas usando modelos de lenguaje ejecutados en local.

### Funcionalidades clave

- Carga de documentos: PDF, Word (.docx), Excel (.xlsx/.csv), Markdown, texto plano
- Indexación semántica con embeddings locales
- **Auto-tagging inteligente**: clasificación y etiquetado automático de documentos mediante el LLM local tras la ingesta
- Filtrado de búsquedas por tags, categoría, tipo de documento e idioma
- Chat conversacional con contexto documental (RAG)
- **Historial de chats**: persistencia de sesiones y mensajes con trazabilidad de fuentes usadas en cada respuesta
- Generación de resúmenes automáticos
- Ejecución 100% local (sin APIs externas obligatorias)
- Interfaz web responsive

---

## 2. Arquitectura

### 2.1 Diagrama de capas

```
┌──────────────────────────────────────────────────────┐
│                      FRONTEND                        │
│            (React / Vue / Vanilla JS)                │
│  ┌──────────┐  ┌───────────┐  ┌──────┐ ┌──────────┐ │
│  │  Chat UI │  │  Upload   │  │ Tags │ │ Historial│ │
│  └──────────┘  └───────────┘  └──────┘ └──────────┘ │
└────────────────────────┬─────────────────────────────┘
                         │ HTTP / WebSocket
┌────────────────────────▼─────────────────────────────┐
│                    API LAYER                          │
│                FastAPI (Python)                       │
│  ┌──────────┐  ┌───────────┐  ┌──────────────┐      │
│  │ /chat    │  │ /upload   │  │ /documents   │      │
│  │ /summary │  │ /search   │  │ /collections │      │
│  └──────────┘  └───────────┘  │ /tags        │      │
│  ┌──────────┐                 │ /sessions    │      │
│  │/sessions │                 └──────────────┘      │
│  │ /{id}/   │                                       │
│  │ messages │                                       │
│  └──────────┘                                       │
└────────────────────────┬─────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────┐
│                  DOMAIN LAYER                         │
│  ┌───────────────┐  ┌────────────────────────┐       │
│  │ RAG Pipeline  │  │ Document Processor     │       │
│  │ (LangChain)   │  │ (Loaders + Splitters)  │       │
│  └───────┬───────┘  └───────────┬────────────┘       │
│          │                      │                     │
│  ┌───────▼───────┐  ┌──────────▼─────────────┐       │
│  │  LLM Local    │  │  Embedding Model       │       │
│  │  (Ollama)     │  │  (sentence-transformers)│       │
│  └───────┬───────┘  └────────────────────────┘       │
│          │                                            │
│  ┌───────▼──────────────────────────────────┐        │
│  │  Auto-Tagger (post-ingesta)              │        │
│  │  LLM analiza chunks → genera tags,       │        │
│  │  categoría, tipo de doc e idioma          │        │
│  └───────┬──────────────────────────────────┘        │
└──────────┼───────────────────────────────────────────┘
           │
┌──────────▼───────────────────────────────────────────┐
│            INFRASTRUCTURE LAYER                       │
│  ┌───────────────┐  ┌────────────────────────┐       │
│  │  ChromaDB /   │  │  SQLite / PostgreSQL   │       │
│  │  FAISS        │  │  (metadatos, tags,     │       │
│  │  (vectores +  │  │   usuarios, sesiones)  │       │
│  │   tag metadata│  │                        │       │
│  └───────────────┘  └────────────────────────┘       │
│  ┌────────────────────────────────────────────┐      │
│  │  Sistema de ficheros (docs originales)     │      │
│  └────────────────────────────────────────────┘      │
└──────────────────────────────────────────────────────┘
```

### 2.2 Patrones de diseño aplicados

| Patrón | Dónde se aplica | Por qué |
|--------|----------------|---------|
| **Strategy** | Document Loaders | Cada formato (PDF, DOCX, XLSX…) implementa una estrategia de carga distinta bajo una interfaz común |
| **Chain of Responsibility** | Pipeline RAG | Cada paso (split → embed → retrieve → generate) es un eslabón desacoplado |
| **Repository** | Acceso a datos | Abstrae si los vectores están en ChromaDB, FAISS o Pinecone |
| **Factory Method** | Creación de loaders | Decide qué loader instanciar según la extensión del fichero |
| **Decorator** | Auto-Tagger | Envuelve el pipeline de ingesta añadiendo el paso de etiquetado sin modificar los loaders existentes |
| **Observer** | Progreso de ingesta | Notifica al frontend del estado de procesamiento de documentos |
| **Facade** | API endpoints | Simplifica la interacción con el pipeline complejo de LangChain |

---

## 3. Stack Tecnológico

### 3.1 Backend

| Componente | Tecnología | Justificación |
|-----------|-----------|---------------|
| Framework web | **FastAPI** | Async nativo, tipado con Pydantic, OpenAPI automático |
| Orquestación LLM | **LangChain** | Chains, retrievers, document loaders, memory |
| LLM local | **Ollama** (contenedor Docker externo, ya desplegado) | Conexión vía API HTTP al servicio existente en la misma máquina |
| Embeddings | **sentence-transformers** (o Ollama embeddings) | Modelos ligeros como `all-MiniLM-L6-v2` |
| Vector Store | **ChromaDB** (inicio) / **FAISS** (alternativa) | ChromaDB: persistencia fácil. FAISS: rendimiento puro |
| Base de datos | **SQLite** (MVP) → **PostgreSQL** (producción) | Metadatos de documentos, sesiones, historial |
| Task queue | **Celery + Redis** (fase 2) | Ingesta asíncrona de documentos pesados |

### 3.2 Frontend

| Componente | Tecnología | Justificación |
|-----------|-----------|---------------|
| Framework | **React + TypeScript** (o Vue 3 si prefieres) | Componentes reactivos para el chat |
| Estilos | **Tailwind CSS** | Prototipado rápido, responsive |
| Estado | **Zustand** o **Pinia** | Ligero, sin boilerplate |
| Comunicación | **fetch + SSE** (Server-Sent Events) | Streaming de respuestas token a token |

### 3.3 Document Loaders (LangChain)

| Formato | Loader |
|---------|--------|
| PDF | `PyPDFLoader` / `PDFPlumberLoader` |
| Word (.docx) | `Docx2txtLoader` / `UnstructuredWordDocumentLoader` |
| Excel (.xlsx/.csv) | `CSVLoader` / `UnstructuredExcelLoader` |
| Markdown | `UnstructuredMarkdownLoader` |
| Texto plano | `TextLoader` |

---

## 4. Estructura del Proyecto

```
rag-chatbot/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                  # FastAPI app + CORS
│   │   ├── config.py                # Settings con pydantic-settings
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── routes/
│   │   │   │   ├── chat.py          # POST /chat, GET /chat/stream
│   │   │   │   ├── documents.py     # POST /upload, GET /documents
│   │   │   │   ├── collections.py   # CRUD de colecciones
│   │   │   │   ├── tags.py          # GET /tags, PATCH /documents/{id}/tags
│   │   │   │   ├── sessions.py      # CRUD sesiones + historial mensajes
│   │   │   │   └── summary.py       # POST /summary
│   │   │   └── dependencies.py      # Inyección de dependencias
│   │   ├── core/
│   │   │   ├── rag_pipeline.py      # Orquestación LangChain
│   │   │   ├── llm_provider.py      # Strategy para LLM (Ollama, etc.)
│   │   │   ├── embeddings.py        # Wrapper de embeddings
│   │   │   └── prompts.py           # Templates de prompts
│   │   ├── document_processing/
│   │   │   ├── loader_factory.py    # Factory de loaders
│   │   │   ├── loaders/             # Strategies por formato
│   │   │   │   ├── base.py
│   │   │   │   ├── pdf_loader.py
│   │   │   │   ├── docx_loader.py
│   │   │   │   ├── excel_loader.py
│   │   │   │   └── markdown_loader.py
│   │   │   ├── splitter.py          # Chunking configurable
│   │   │   ├── metadata.py          # Extracción de metadatos
│   │   │   └── auto_tagger.py       # Auto-etiquetado con LLM local
│   │   ├── repositories/
│   │   │   ├── vector_store.py      # Repository para ChromaDB/FAISS
│   │   │   ├── document_repo.py     # Repository para metadatos SQL
│   │   │   ├── tag_repo.py          # Repository para tags (CRUD, dedup)
│   │   │   └── chat_history.py      # Persistencia de conversaciones
│   │   └── models/
│   │       ├── schemas.py           # Pydantic schemas (request/response)
│   │       └── entities.py          # SQLAlchemy / modelos de dominio
│   ├── tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   └── conftest.py
│   ├── alembic/                     # Migraciones de BD
│   ├── pyproject.toml
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Chat/
│   │   │   │   ├── ChatWindow.tsx
│   │   │   │   ├── MessageBubble.tsx
│   │   │   │   ├── InputBar.tsx
│   │   │   │   └── SourcesCited.tsx  # Muestra chunks/docs citados por respuesta
│   │   │   ├── Sessions/
│   │   │   │   ├── SessionList.tsx   # Lista de conversaciones anteriores
│   │   │   │   └── SessionItem.tsx   # Tarjeta de sesión con título y fecha
│   │   │   ├── Documents/
│   │   │   │   ├── UploadZone.tsx
│   │   │   │   ├── DocumentList.tsx
│   │   │   │   └── TagManager.tsx   # Filtros por tag, edición manual
│   │   │   ├── Tags/
│   │   │   │   ├── TagCloud.tsx     # Nube/lista de tags existentes
│   │   │   │   └── TagFilter.tsx    # Selector de tags para filtrar búsquedas
│   │   │   └── Layout/
│   │   │       ├── Sidebar.tsx
│   │   │       └── Header.tsx
│   │   ├── services/
│   │   │   └── api.ts               # Cliente HTTP tipado
│   │   ├── stores/
│   │   │   └── chatStore.ts
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
├── Makefile
└── README.md
```

---

## 5. Pipeline RAG — Flujo Detallado

### 5.1 Ingesta de documentos (con auto-tagging)

```
Fichero subido
    │
    ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ LoaderFactory │────▶│ TextSplitter │────▶│  Embeddings  │
│ (detecta fmt) │     │ (chunks de   │     │ (vectoriza   │
│               │     │  500-1000    │     │  cada chunk) │
│               │     │  tokens)     │     │              │
└──────────────┘     └──────┬───────┘     └──────┬───────┘
                            │                     │
                    ┌───────▼────────┐  ┌─────────▼────────────┐
                    │  Auto-Tagger   │  │  ChromaDB / FAISS    │
                    │  (envía top-N  │  │  (almacena vectores + │
                    │  chunks al LLM │  │   metadata + texto)  │
                    │  para generar  │  └─────────┬────────────┘
                    │  tags)         │            │
                    └───────┬────────┘            │
                            │                     │
                    ┌───────▼────────┐            │
                    │  Tags + meta   │            │
                    │  → SQLite/PG   │◄───────────┘
                    │  → ChromaDB    │  (inyecta tags como
                    │    metadata    │   metadata en chunks)
                    └────────────────┘
```

### 5.2 Consulta (pregunta-respuesta con filtro por tags)

```
Pregunta del usuario
    │
    │  + tags seleccionados (opcional)
    │
    ▼
┌──────────────┐     ┌──────────────────┐     ┌──────────────┐
│  Embedding   │────▶│  Similarity      │────▶│  Prompt      │
│  de la query │     │  Search (top-k)  │     │  Template    │
│              │     │  + filtro por    │     │  + contexto  │
│              │     │  tag metadata    │     │              │
└──────────────┘     └──────────────────┘     └──────┬───────┘
                                                      │
                                              ┌───────▼───────┐
                                              │   LLM Local   │
                                              │   (Ollama)    │
                                              │               │
                                              │  → Respuesta  │
                                              │    con citas   │
                                              └───────────────┘
```

---

## 6. Fases de Desarrollo

### Fase 1 — MVP (2-3 semanas)

**Objetivo:** Chat funcional con un tipo de documento y un modelo local.

- [ ] Setup del proyecto (estructura, Docker, entorno virtual)
- [ ] Configurar conexión al servicio Ollama externo (mismo host, contenedor Docker independiente)
- [ ] Implementar carga de PDFs con `PyPDFLoader`
- [ ] Configurar ChromaDB como vector store
- [ ] Crear pipeline RAG básico con LangChain (`RetrievalQA`)
- [ ] Endpoint FastAPI `/chat` con respuesta completa
- [ ] Frontend mínimo: input de texto + área de respuesta
- [ ] Endpoint `/upload` para subir un PDF
- [ ] Tests unitarios del pipeline

### Fase 2 — Multi-formato + Auto-tagging + UX (3-4 semanas)

**Objetivo:** Soporte completo de formatos, etiquetado automático y experiencia de chat fluida.

- [ ] Implementar `LoaderFactory` con Strategy pattern
- [ ] Añadir loaders: DOCX, XLSX/CSV, Markdown, TXT
- [ ] **Implementar `AutoTagger`** con prompt estructurado al LLM local
- [ ] **Modelo de datos**: tablas `tags`, `document_tags` (many-to-many) con deduplicación
- [ ] **Inyectar tags como metadata** en chunks de ChromaDB
- [ ] **Endpoint `GET /tags`**: listar tags existentes con conteo de documentos
- [ ] **Endpoint `PATCH /documents/{id}/tags`**: edición manual de tags
- [ ] **Filtro por tags en el retriever**: `search_kwargs.filter` por metadata
- [ ] **UI TagCloud + TagFilter**: selección visual de tags para acotar búsquedas
- [ ] Normalización de tags (lowercase, dedup de sinónimos vía LLM)
- [ ] Streaming de respuestas con SSE (`StreamingResponse`)
- [ ] UI de chat completa (burbujas, scroll, timestamps)
- [ ] Componente drag-and-drop para upload múltiple
- [ ] Lista de documentos cargados con metadatos y tags asignados
- [ ] **Modelo de datos de historial**: tablas `chat_sessions` y `chat_messages` con relación 1:N
- [ ] **Persistir fuentes (sources)** en cada mensaje del asistente (chunks usados, doc origen, score)
- [ ] **Endpoints CRUD de sesiones**: crear, listar, leer mensajes, eliminar
- [ ] **Auto-generar título de sesión** a partir del primer mensaje del usuario
- [ ] **UI SessionList + SessionItem**: sidebar con conversaciones anteriores, reabrir sesión
- [ ] **Componente SourcesCited**: mostrar los documentos citados en cada respuesta
- [ ] Gestión de colecciones (agrupar documentos por tema)
- [ ] Progress bar durante la ingesta (incluyendo paso de auto-tagging)

### Fase 3 — Funcionalidades avanzadas (3-4 semanas)

**Objetivo:** Resúmenes, mejora de calidad y configuración.

- [ ] Endpoint `/summary` para resumen automático de documentos
- [ ] **Memoria conversacional**: cargar historial de sesión en `ConversationBufferMemory` al reabrir un chat
- [ ] **Búsqueda en historial**: endpoint para buscar mensajes por texto en todas las sesiones
- [ ] **Limitar contexto conversacional**: `ConversationSummaryMemory` para sesiones largas (evitar exceder ventana del modelo)
- [ ] Panel de configuración: elegir modelo, chunk size, top-k
- [ ] Soporte para múltiples modelos de Ollama simultáneamente
- [ ] Citación de fuentes (indicar de qué documento viene cada respuesta)
- [ ] Re-ranking de resultados para mejorar relevancia
- [ ] Evaluación de calidad con métricas (faithfulness, relevance)
- [ ] Tests de integración end-to-end

### Fase 4 — Producción y escalado (2-3 semanas)

**Objetivo:** Robustez, rendimiento y despliegue.

- [ ] Migrar a PostgreSQL + pgvector (alternativa a ChromaDB)
- [ ] Celery + Redis para ingesta asíncrona
- [ ] Caché de embeddings para documentos ya procesados
- [ ] Rate limiting y autenticación básica (JWT)
- [ ] Dockerización completa (`docker-compose up`)
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Logging estructurado y monitorización
- [ ] Documentación de API (OpenAPI ya viene con FastAPI)

---

## 7. Decisiones Técnicas Clave

### 7.1 Chunking strategy

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,       # tokens por chunk
    chunk_overlap=200,     # solapamiento para mantener contexto
    separators=["\n\n", "\n", ". ", " ", ""]
)
```

El `RecursiveCharacterTextSplitter` respeta la jerarquía del texto: primero intenta partir por párrafos, luego por líneas, luego por frases. El overlap evita perder contexto en los bordes.

### 7.2 Conexión con Ollama (servicio externo)

Ollama ya está desplegado en un contenedor Docker independiente en la misma máquina. La aplicación se conecta vía HTTP configurando la URL base:

```python
# config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    ollama_base_url: str = "http://host.docker.internal:11434"  # desde otro container
    ollama_model: str = "llama3.1:8b"
    ollama_embed_model: str = "nomic-embed-text"
    # ...

    class Config:
        env_file = ".env"
```

```yaml
# docker-compose.yml (solo la app, sin Ollama)
services:
  backend:
    build: ./backend
    environment:
      - OLLAMA_BASE_URL=http://host.docker.internal:11434
    extra_hosts:
      - "host.docker.internal:host-gateway"  # Linux
    # ...
```

> **Nota:** Si ambos contenedores están en la misma red Docker, se puede usar
> directamente el nombre del servicio (ej. `http://ollama:11434`). Si Ollama
> corre en el host, `host.docker.internal` resuelve al host desde dentro del
> contenedor.

### 7.3 Modelo local recomendado

Para empezar, usar **Ollama** con uno de estos modelos según tu hardware:

| RAM GPU | Modelo recomendado | Uso |
|---------|-------------------|-----|
| 8 GB | Llama 3.1 8B / Phi-3 Mini | Respuestas generales |
| 16 GB | Mistral 7B Instruct | Buen equilibrio calidad/velocidad |
| 24 GB+ | Llama 3.1 70B (Q4) | Máxima calidad |

Para embeddings: `nomic-embed-text` vía Ollama o `all-MiniLM-L6-v2` vía sentence-transformers.

### 7.4 Prompt template base

```python
RAG_PROMPT = """Eres un asistente que responde preguntas basándose
exclusivamente en el contexto proporcionado. Si la información no
está en el contexto, di que no tienes suficiente información.

Contexto:
{context}

Pregunta: {question}

Respuesta (cita las fuentes entre corchetes [nombre_documento, página]):"""
```

### 7.5 Sistema de Auto-Tagging

#### Flujo del auto-tagger

Tras la ingesta, el `AutoTagger` selecciona los primeros N chunks (o un resumen) del documento y los envía al LLM local con un prompt que fuerza respuesta JSON estructurada. Los tags resultantes se persisten en dos sitios: la base de datos relacional (para listar, filtrar y gestionar desde la UI) y como metadata en cada chunk del vector store (para filtrar durante el retrieval).

#### Prompt de auto-tagging

```python
AUTO_TAG_PROMPT = """Analiza el siguiente contenido y genera etiquetas
de clasificación. Responde SOLO con un JSON válido, sin explicaciones
ni markdown.

Tags existentes en el sistema (reutiliza si aplica):
{existing_tags}

Contenido del documento:
{content}

Formato de respuesta:
{{
    "categoria": "<una de: legal, tecnico, financiero, rrhh, marketing, general>",
    "tags": ["tag1", "tag2", "tag3"],
    "idioma": "<código ISO 639-1>",
    "tipo_documento": "<informe|contrato|manual|presentacion|datos|otro>"
}}

Reglas:
- Máximo 5 tags, descriptivos y concisos
- Reutiliza tags existentes cuando el significado coincida
- Los tags deben ser en minúsculas y sin acentos
- No inventes categorías fuera de las listadas"""
```

Pasar `existing_tags` al prompt es clave para evitar la proliferación de sinónimos. Si ya existe "machine-learning", el modelo debería reutilizarlo en vez de crear "ml" o "aprendizaje-automatico".

#### Modelo de datos

```python
# Tabla intermedia many-to-many
document_tags = Table(
    "document_tags",
    Base.metadata,
    Column("document_id", String, ForeignKey("documents.id"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id"), primary_key=True),
)

class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(primary_key=True, default=uuid4)
    filename: Mapped[str]
    format: Mapped[str]                        # pdf, docx, xlsx...
    uploaded_at: Mapped[datetime]
    chunk_count: Mapped[int]
    category: Mapped[str | None]               # del auto-tagger
    language: Mapped[str | None]               # del auto-tagger
    doc_type: Mapped[str | None]               # del auto-tagger
    tags: Mapped[list["Tag"]] = relationship(
        secondary=document_tags, back_populates="documents"
    )

class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    source: Mapped[str] = mapped_column(default="auto")  # "auto" | "manual"
    documents: Mapped[list["Document"]] = relationship(
        secondary=document_tags, back_populates="tags"
    )
```

#### Retrieval filtrado por tags

```python
# Búsqueda global (sin filtro)
retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

# Búsqueda acotada a un tag específico
retriever = vectorstore.as_retriever(
    search_kwargs={
        "k": 5,
        "filter": {"category": "legal"}
    }
)

# Búsqueda acotada a múltiples tags (AND)
retriever = vectorstore.as_retriever(
    search_kwargs={
        "k": 5,
        "filter": {
            "$and": [
                {"category": "financiero"},
                {"tags": {"$contains": "presupuesto"}}
            ]
        }
    }
)
```

#### API de tags

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `GET` | `/tags` | Lista todos los tags con conteo de documentos asociados |
| `GET` | `/tags/{name}/documents` | Documentos asociados a un tag |
| `PATCH` | `/documents/{id}/tags` | Añadir/eliminar tags manualmente a un documento |
| `POST` | `/documents/{id}/retag` | Re-ejecutar el auto-tagger sobre un documento |
| `DELETE` | `/tags/{id}` | Eliminar un tag (desvincula de todos los documentos) |

### 7.6 Historial de Chats

#### Modelo de datos

```python
class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[str] = mapped_column(primary_key=True, default=uuid4)
    title: Mapped[str | None]                    # auto-generado del primer mensaje
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, onupdate=datetime.utcnow
    )
    collection_id: Mapped[str | None] = mapped_column(
        ForeignKey("collections.id")             # colección de docs asociada
    )
    messages: Mapped[list["ChatMessage"]] = relationship(
        back_populates="session",
        order_by="ChatMessage.created_at",
        cascade="all, delete-orphan"
    )

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[str] = mapped_column(primary_key=True, default=uuid4)
    session_id: Mapped[str] = mapped_column(ForeignKey("chat_sessions.id"))
    role: Mapped[str]                            # "user" | "assistant"
    content: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    model_used: Mapped[str | None]               # modelo Ollama que respondió
    sources: Mapped[str | None]                  # JSON: chunks usados en la respuesta
    session: Mapped["ChatSession"] = relationship(back_populates="messages")
```

El campo `sources` almacena un JSON con la trazabilidad de cada respuesta:

```json
{
  "chunks_used": [
    {
      "document_id": "abc-123",
      "document_name": "informe_Q3.pdf",
      "page": 12,
      "chunk_text": "Los ingresos del tercer trimestre...",
      "similarity_score": 0.87
    }
  ],
  "retriever_config": {
    "top_k": 5,
    "filter_tags": ["financiero"]
  }
}
```

Esto permite mostrar las fuentes citadas en la UI y, en el futuro, evaluar la calidad del retrieval de forma programática.

#### Integración con LangChain Memory

Al reabrir una sesión, se reconstruye la memoria conversacional desde la base de datos para que el LLM tenga contexto de los mensajes anteriores:

```python
from langchain.memory import ConversationBufferMemory

def load_memory_from_session(session_id: str) -> ConversationBufferMemory:
    messages = chat_repo.get_messages(session_id)
    memory = ConversationBufferMemory(
        return_messages=True,
        memory_key="chat_history"
    )
    for msg in messages:
        if msg.role == "user":
            memory.chat_memory.add_user_message(msg.content)
        else:
            memory.chat_memory.add_ai_message(msg.content)
    return memory
```

Para sesiones largas (más de ~20 mensajes), conviene usar `ConversationSummaryMemory` para comprimir el historial y no exceder la ventana de contexto del modelo:

```python
from langchain.memory import ConversationSummaryMemory

def load_summary_memory(session_id: str, llm) -> ConversationSummaryMemory:
    messages = chat_repo.get_messages(session_id)
    memory = ConversationSummaryMemory(
        llm=llm,
        memory_key="chat_history"
    )
    for msg in messages:
        if msg.role == "user":
            memory.chat_memory.add_user_message(msg.content)
        else:
            memory.chat_memory.add_ai_message(msg.content)
    # El summary se genera automáticamente al superar el buffer
    return memory
```

#### Auto-generación de título de sesión

El título se genera automáticamente la primera vez que el usuario envía un mensaje, usando el propio LLM:

```python
TITLE_PROMPT = """Genera un título corto (máximo 6 palabras) que resuma
la intención de esta pregunta. Responde SOLO con el título, sin comillas
ni puntuación final.

Pregunta: {first_message}

Título:"""
```

#### API de sesiones

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `GET` | `/sessions` | Lista sesiones ordenadas por `updated_at` desc (paginado) |
| `POST` | `/sessions` | Crea nueva sesión (opcionalmente vinculada a una colección) |
| `GET` | `/sessions/{id}` | Detalle de sesión con metadatos |
| `GET` | `/sessions/{id}/messages` | Historial completo de mensajes de una sesión |
| `DELETE` | `/sessions/{id}` | Elimina sesión y todos sus mensajes (cascade) |
| `GET` | `/sessions/search?q=texto` | Busca mensajes por contenido en todas las sesiones |

#### Diagrama de relaciones completo

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Collection  │◄───┐│   Document   │────▶│     Tag      │
│              │    ││              │ M:N │              │
│  id          │    ││  id          │     │  id          │
│  name        │    ││  filename    │     │  name        │
│  description │    ││  format      │     │  source      │
└──────────────┘    ││  category    │     └──────────────┘
       ▲            ││  tags[]      │
       │            │└──────────────┘
       │            │
┌──────┴───────┐    │
│ ChatSession  │────┘
│              │
│  id          │
│  title       │
│  collection  │
│  updated_at  │
│  messages[]  │
└──────┬───────┘
       │ 1:N
┌──────▼───────┐
│ ChatMessage  │
│              │
│  id          │
│  role        │
│  content     │
│  sources     │ ← JSON con chunks y scores
│  model_used  │
└──────────────┘
```

---

## 8. Dependencias Python Principales

```toml
[project]
name = "rag-chatbot"
requires-python = ">=3.11"

dependencies = [
    "fastapi>=0.110",
    "uvicorn[standard]",
    "langchain>=0.2",
    "langchain-community",
    "langchain-chroma",          # ChromaDB integration
    "langchain-ollama",          # Ollama integration
    "chromadb",
    "sentence-transformers",
    "pypdf",                     # PDF loader
    "docx2txt",                  # Word loader
    "openpyxl",                  # Excel loader
    "unstructured",              # Multi-format loader
    "python-multipart",          # File uploads en FastAPI
    "sqlalchemy",
    "alembic",
    "pydantic-settings",
    "sse-starlette",             # Server-Sent Events
]

[project.optional-dependencies]
dev = [
    "pytest",
    "pytest-asyncio",
    "httpx",                     # Test client async
    "ruff",
    "mypy",
]
```

---

## 9. Riesgos y Mitigaciones

| Riesgo | Impacto | Mitigación |
|--------|---------|------------|
| Modelos locales lentos en CPU | Respuestas de 30s+ | Priorizar GPU; modelos cuantizados (Q4/Q5); streaming |
| Calidad baja en respuestas | Respuestas irrelevantes | Ajustar chunk size, overlap, top-k; re-ranking; evaluar con RAGAS |
| Documentos con formato complejo | Pérdida de información (tablas Excel, PDFs escaneados) | OCR con Tesseract para PDFs escaneados; parseo especializado por formato |
| Escalado de vector store | Lentitud con miles de documentos | Migrar de ChromaDB a pgvector o FAISS con índices IVF |
| Memoria del chat crece indefinidamente | Contexto excede ventana del modelo | Usar `ConversationSummaryMemory` o limitar a últimos N turnos |
| Tags inconsistentes del LLM | Sinónimos, idiomas mezclados, tags inútiles | Pasar tags existentes en el prompt; normalización (lowercase, sin acentos); revisión manual desde la UI |
| Auto-tagging lento en documentos largos | Bloqueo de la ingesta | Enviar solo los primeros N chunks (no el doc completo); ejecutar tagging en background (Celery) |
| Historial de sesión excede ventana del modelo | Respuestas pierden coherencia | Cambiar a `ConversationSummaryMemory` a partir de ~20 mensajes; limitar tokens de historial inyectados |
| Base de datos de mensajes crece sin límite | Lentitud en queries, almacenamiento excesivo | Paginación en endpoints; política de retención opcional; índices en `created_at` y `session_id` |

---

## 10. Criterios de Éxito del MVP

- [ ] El usuario puede subir un PDF y hacer preguntas sobre su contenido
- [ ] Las respuestas se generan en menos de 15 segundos (con GPU)
- [ ] Las respuestas citan el documento fuente
- [ ] El sistema funciona completamente offline
- [ ] La interfaz web es funcional en desktop y móvil
- [ ] Los documentos reciben tags automáticos tras la ingesta
- [ ] El usuario puede filtrar búsquedas por tags desde la UI
- [ ] El usuario puede editar tags manualmente (añadir/eliminar)
- [ ] El usuario puede ver y retomar conversaciones anteriores
- [ ] Cada respuesta del asistente muestra las fuentes documentales citadas