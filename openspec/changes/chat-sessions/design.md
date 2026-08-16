## Context

Hoy `sessionsStore`/`chatStore` (frontend) mantienen sesiones y mensajes
solo en memoria; `POST /chat` (`backend/app/api/routes/chat.py`) no conoce
el concepto de sesión, solo recibe `message`/`model` y devuelve una
respuesta aislada. El backend ya sigue el patrón Repository para todo
acceso a datos (`document_repo.py`, `tag_repo.py`, `stats_repo.py`), todos
compartiendo el mismo engine/`sessionmaker` (`_SessionLocal`) definido en
`document_repo.py`, con `Base.metadata.create_all(engine)` llamado en el
`__init__` del repositorio (no hay Alembic todavía pese a estar en el
stack objetivo — es el patrón real seguido hasta ahora, y este change no
lo cambia). El modelo de datos y la API de sesiones ya están completamente
especificados en `rag_vault_plan.md` §7.6.

## Goals / Non-Goals

**Goals:**
- Persistir sesiones y mensajes (con fuentes citadas) en SQLite, siguiendo
  el modelo de `rag_vault_plan.md` §7.6.
- Que `POST /chat` persista automáticamente cada turno de la conversación
  en la sesión indicada.
- Auto-generar el título de sesión en el primer mensaje.
- Que el frontend refleje datos reales: el historial sobrevive a recargar
  la página.

**Non-Goals:**
- Colecciones (`collection_id`, tabla `collections`) — no existen todavía;
  se deja `ChatSession` sin ese campo hasta que haya un change dedicado a
  colecciones.
- Memoria conversacional (`ConversationBufferMemory`/`ConversationSummaryMemory`)
  — es un ítem de Fase 3 del plan, no de este change. El pipeline sigue
  respondiendo sin contexto de turnos anteriores.
- Búsqueda en historial (`GET /sessions/search`) — también Fase 3.
- Renombrar sesión vía API (`PATCH /sessions/{id}`) — no está en el plan;
  el renombrado sigue siendo solo estado local de la UI, como hoy.
- Migraciones Alembic — se sigue el patrón existente de `create_all` en
  vez de introducir Alembic solo para este change (sería inconsistente con
  el resto del repo y fuera de alcance).
- Streaming de respuestas (SSE) — change aparte ya identificado en el plan.

## Decisions

- **Sesión requerida en `/chat`**: `ChatRequest.session_id` pasa a ser
  obligatorio. Alternativa descartada: crear la sesión implícitamente
  dentro de `/chat` si no se manda `session_id` — se descarta porque
  duplicaría la responsabilidad de `POST /sessions` y ocultaría en un
  endpoint distinto una operación (crear sesión) que ya tiene su propio
  endpoint explícito; además el frontend con `new-chat-session` ya
  garantiza que siempre hay una sesión activa antes de poder escribir
  (`InputBar` ya bloquea el envío si `!activeId`).
- **Persistencia del turno completo en `/chat`**: el mensaje de usuario se
  guarda antes de invocar el pipeline (para no perderlo si el pipeline
  falla) y el de asistente después, en la misma request — no se usa una
  tarea en background ni cola, siguiendo el mismo estilo síncrono que ya
  tiene `/chat`. Si el pipeline lanza, el mensaje de usuario queda
  persistido pero sin respuesta asociada; el frontend ya maneja el caso de
  error mostrando un mensaje de error en el hilo (requisito existente de
  `chat-ui-shell`), y al reabrir la sesión ese mensaje de usuario seguirá
  ahí para reintentar.
- **Formato de `sources` persistido**: se usa tal cual el JSON ya
  documentado en `CLAUDE.md` (`chunks_used` + `retriever_config`), donde
  `retriever_config` se rellena con `{"top_k": settings.retrieval_top_k,
  "filter_tags": []}` (no hay filtro por tags en el retriever todavía —
  campo reservado, no funcional en este change). Se serializa a texto con
  `json.dumps` en la columna `sources: Mapped[str | None]`, igual que
  especifica el plan.
- **Repositorio único para sesiones y mensajes**: `ChatSessionRepository`
  en `chat_repo.py` expone tanto operaciones de sesión
  (`create`/`list`/`get`/`delete`) como de mensaje (`add_message`,
  `list_messages`), en vez de separarlos en dos repos — sesión y mensaje
  son un agregado 1:N sin sentido independiente (un mensaje no existe sin
  su sesión), igual que Document/Tag comparten repos según su relación en
  el código actual.
- **Auto-título**: se genera con una llamada síncrona adicional al LLM
  (mismo `get_llm(model)` que ya usa `/chat`) solo cuando
  `session.title is None` y es el primer mensaje de usuario de la sesión;
  usa literalmente `TITLE_PROMPT` de `rag_vault_plan.md` §7.6. Si esa
  llamada falla, se seguirá adelante con la respuesta del chat y la sesión
  se queda sin título (se reintentará en el siguiente mensaje mientras
  `title` siga siendo `None`) — no se bloquea el turno de chat por un
  fallo en la generación de título.
- **Migración del frontend**: `sessionsStore` deja de tener estado
  "mock" propio; sus acciones (`createSession`, `deleteSession`,
  `renameSession` sigue local, `setActive`) llaman a
  `frontend/src/services/api.ts` (nuevas funciones `listSessions`,
  `createSession`, `deleteSession`, `getSessionMessages`) y guardan el
  resultado en el store. `chatStore.messagesBySession` se pobla bajo
  demanda al activar una sesión (fetch de `GET /sessions/{id}/messages`),
  no de golpe al arrancar, para no traer todo el historial de todas las
  sesiones de una vez.
- **Adaptación de `Session` en frontend**: los campos `tag`/`time` de
  `Session` (frontend) no existen en el modelo de backend
  (`ChatSession` solo tiene `id`, `title`, `created_at`, `updated_at`).
  `tag` se elimina de la interfaz (no hay tags de sesión en el plan,
  solo de documento); `time` se deriva en el propio componente a partir de
  `updated_at` con un formateo relativo simple ("hoy", "ayer", etc., ya
  usado como texto libre hoy) en vez de guardarse como campo de estado.

## Risks / Trade-offs

- [Cambio de contrato de `/chat` rompe cualquier cliente que llamara sin
  `session_id`] → Es una `BREAKING` change explícita en el proposal; el
  único cliente real es el frontend de este mismo repo, actualizado en el
  mismo change. `backend/tests/unit/test_chat_route.py` se actualiza para
  reflejarlo.
- [Auto-título añade una llamada extra al LLM en el primer mensaje,
  aumentando la latencia percibida] → Aceptado: es exactamente el
  comportamiento descrito en el plan; si en el futuro molesta, se puede
  mover a background sin cambiar el contrato de la API (la sesión ya
  tiene un título por defecto en el frontend mientras tanto).
- [Sin Alembic, un cambio de esquema futuro no tendrá migración
  versionada, solo `create_all`] → Riesgo ya existente y aceptado en el
  resto del backend; introducir Alembic es una decisión transversal fuera
  del alcance de esta capability concreta.
