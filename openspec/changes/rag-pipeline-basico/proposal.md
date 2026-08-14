## Why

`chat-ui-shell` dejó una interfaz de chat completa pero deliberadamente
honesta sobre no tener pipeline RAG conectado (Fase 1 del plan). Con el
scaffolding y la UI ya en pie, toca cerrar el MVP: subir un PDF de verdad,
indexarlo y poder preguntarle al modelo local sobre su contenido con
fuentes citadas reales.

## What Changes

- **Ingesta de documentos**: `LoaderFactory` (Factory Method) que
  selecciona el loader por extensión — solo `.pdf` soportado en este
  change (`PyPDFLoader`), Strategy lista para añadir DOCX/XLSX/MD en Fase
  2 sin tocar el factory ni las rutas de API.
- **Chunking**: `RecursiveCharacterTextSplitter` (1000/200, según
  `rag_vault_plan.md` §7.1).
- **Embeddings y vector store**: Ollama (`OllamaEmbeddings`) +
  ChromaDB persistente, tras un `VectorStoreRepository` (Repository) — la
  ruta de API y el pipeline nunca hablan con Chroma directamente.
- **Metadata de documentos**: tabla `documents` en SQLite (SQLAlchemy) vía
  `DocumentRepository`, sin Alembic todavía (ver design.md decisión 4).
- **Pipeline RAG**: pasos desacoplados (retrieve → prompt → generate,
  Chain of Responsibility) reutilizando el `RAG_PROMPT` de
  `rag_vault_plan.md` §7.4 literal.
- **Endpoints** (Facade sobre el pipeline): `POST /upload` (sube y procesa
  un PDF), `POST /chat` (pregunta → respuesta con fuentes).
- **Frontend**: `UploadZone` pasa a subir de verdad (drag-and-drop o
  selección de fichero) contra `POST /upload`; `chatStore.sendMessage`
  pasa a llamar `POST /chat` real en vez de devolver el marcador de
  posición de maqueta — con estado de carga y de error explícito (nunca
  fabrica una respuesta).

Fuera de alcance (Fase 2 u otros changes): multi-formato (DOCX/XLSX/MD),
auto-tagging, persistencia real de sesiones/mensajes en BD (las sesiones
siguen siendo del store de Zustand del frontend, como ya se documentó en
`chat-ui-shell`), streaming SSE, re-ranking, colecciones.

## Capabilities

### New Capabilities

- `document-ingestion`: carga, chunking, embeddings y almacenamiento de
  documentos PDF, con su endpoint de subida y la UI de `UploadZone` ya
  funcional.
- `rag-pipeline`: pipeline de recuperación + generación contra los
  documentos indexados, expuesto en `POST /chat`, con fuentes citadas.

### Modified Capabilities

- `chat-ui-shell`: el requirement "Chat honesto sobre ser una maqueta"
  cambia — el chat ya no devuelve un marcador de posición fijo, sino que
  llama al pipeline RAG real, con estado de carga y de error explícito
  (sigue sin fabricar nunca una respuesta, de ahí que se mantenga el
  espíritu del requirement original).

## Impact

- Dependencias backend nuevas: `langchain`, `langchain-community`,
  `langchain-chroma`, `langchain-ollama`, `chromadb`, `pypdf`,
  `sqlalchemy`, `python-multipart`.
- Ficheros/directorios nuevos con datos locales (gitignorados):
  `backend/data/ragvault.db`, `backend/data/chroma/`.
- `Settings` (config.py) gana campos: `chunk_size`, `chunk_overlap`,
  `retrieval_top_k`, `chroma_persist_dir`, `sqlite_path`.
- Frontend: `services/api.ts` gana `uploadDocument()` y
  `sendChatMessage()`; `stores/chatStore.ts` deja de ser puramente local.
- Sin cambios en `docker-compose.yml` (los directorios de datos se montan
  ya vía el volumen existente de `./backend/app`; se añade uno para
  `./backend/data`).
