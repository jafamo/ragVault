## Context

Primer change que introduce lógica de dominio real (hasta ahora solo
había scaffolding y UI con datos de ejemplo). Los patrones de diseño
obligatorios de `CLAUDE.md` aplican aquí por primera vez de verdad:
Strategy/Factory en loaders, Repository en acceso a datos, Chain of
Responsibility en el pipeline, Facade en los endpoints. Restricciones ya
fijadas y no abiertas a discusión: Ollama externo (sin gestionarlo aquí),
logging estructurado ya existente (`structlog`), prompts del plan
reutilizados literalmente.

## Goals / Non-Goals

**Goals:**
- Subir un PDF real, verlo indexado, y preguntar sobre su contenido desde
  la UI ya existente, con fuentes citadas reales (documento + página +
  score).
- Cada paso de ingesta y de consulta vive en su propio módulo, testable de
  forma aislada (mockeando Ollama/Chroma donde haga falta).
- El chat deja de fabricar respuestas: éxito real o error explícito, nunca
  un intermedio simulado.

**Non-Goals:**
- Multi-formato, auto-tagging, colecciones, re-ranking — Fase 2/3.
- Persistencia de sesiones/mensajes en BD — sigue en el store de Zustand
  del frontend (decisión ya tomada en `chat-ui-shell`, no se revisita
  aquí).
- Streaming de respuestas (SSE) — Fase 2.
- Autenticación — no existe en el proyecto todavía.

## Decisions

**1. `LoaderFactory` con un único loader real, pero interfaz Strategy
completa**
`document_processing/loaders/base.py` define una interfaz mínima
(`load(path) -> list[Document]`); `pdf_loader.py` la implementa envolviendo
`PyPDFLoader`. `loader_factory.py` mapea extensión → loader y lanza un
error controlado (`UnsupportedFormatError`, HTTP 415 en la ruta) para
cualquier extensión que no sea `.pdf`. Añadir DOCX/XLSX/MD en Fase 2 es
solo registrar una entrada más en el factory — no se crean stubs vacíos
para esos formatos ahora (YAGNI): habrían quedado sin tests y sin uso
real.

**2. Repository para Chroma y para SQLite**
`repositories/vector_store.py`: `VectorStoreRepository` con
`add_chunks(document_id, chunks)` y `similarity_search(query, k)`, envuelve
`langchain-chroma`. `repositories/document_repo.py`:
`DocumentRepository` con `create`, `get`, `list`, envuelve SQLAlchemy.
Ninguna ruta de API ni el pipeline importan `chromadb` o `sqlalchemy`
directamente — coherente con la regla de `CLAUDE.md`.

**3. SQLite sin Alembic todavía**
El esquema tiene una sola tabla (`documents`) en este change. Añadir
Alembic ahora sería ceremonia sin beneficio: no hay migraciones que
versionar todavía. Se usa `Base.metadata.create_all()` al arrancar la
app. Alembic se introduce en Fase 2, cuando lleguen `tags`,
`document_tags`, `chat_sessions`, `chat_messages` y sí haya un esquema
evolucionando de verdad que necesite migraciones controladas.

**4. Pipeline RAG como pasos desacoplados, no una clase monolítica**
`core/rag_pipeline.py` define un `PipelineContext` (dict tipado) y una
lista de pasos (`retrieve_step`, `prompt_step`, `generate_step`), cada uno
`Callable[[PipelineContext], PipelineContext]`, ejecutados en secuencia
por un `run_pipeline()`. Es la forma más ligera de cumplir Chain of
Responsibility (eslabones desacoplados, se pueden insertar/quitar/testear
por separado) sin construir una jerarquía de clases que este alcance no
necesita.

**5. Prompt reutilizado literal**
`RAG_PROMPT` de `rag_vault_plan.md` §7.4 se copia tal cual a
`core/prompts.py`. No se ajusta la redacción en este change.

**6. `POST /chat` es stateless respecto a sesiones**
No recibe `session_id` ni mantiene historial en el backend — cada pregunta
se resuelve contra todo el corpus indexado, sin memoria conversacional
(eso es `ConversationBufferMemory`, Fase 3). El frontend sigue asociando
la pregunta/respuesta a la sesión activa solo en su propio store, como ya
hacía `chat-ui-shell`.

**7. `UploadZone` con click-to-browse y drag-and-drop reales**
Ya tenía el aspecto visual; se añade `<input type="file" accept=".pdf">`
oculto (activado al hacer clic) y los handlers `dragover`/`drop` nativos.
Al completar la subida se muestra el resultado (nombre, nº de chunks) o el
error, reutilizando los tokens de color de éxito/alerta ya definidos por
skin.

## Risks / Trade-offs

- [Riesgo] PDFs escaneados (sin texto, solo imagen) producen chunks
  vacíos → Mitigación: fuera de alcance en este change (OCR es Fase 3 /
  riesgo ya documentado en `rag_vault_plan.md` §9); `PyPDFLoader` simplemente
  extraerá texto vacío y el documento quedará indexado con 0 chunks útiles,
  sin romper el flujo.
- [Riesgo] Sin Alembic, un cambio de esquema en Fase 2 obligará a migrar
  manualmente el SQLite de desarrollo → Mitigación aceptada: en MVP se
  puede simplemente borrar el fichero de desarrollo; no hay datos de
  producción todavía.
- [Trade-off] `POST /chat` sin `session_id` simplifica mucho este change,
  pero significa que la "memoria" de cada sesión en el frontend es pura
  apariencia (no influye en la respuesta real) hasta que llegue la memoria
  conversacional de Fase 3. Se documenta para que no sorprenda.

## Migration Plan

No aplica — no hay datos previos. Al aplicar este change, `backend/data/`
se crea la primera vez que arranca la app (SQLite) o se sube un documento
(Chroma). Rollback: borrar `backend/data/` (gitignorado, no versionado).

## Open Questions

Ninguna abierta — los límites (sin sesiones reales, sin multi-formato, sin
streaming) quedan fijados como Non-Goals, no como decisiones pendientes.
