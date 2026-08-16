## Why

El historial de chat de la aplicación (sesiones, mensajes, fuentes citadas)
es hoy exclusivamente estado en memoria del frontend (`sessionsStore`,
`chatStore`): se pierde al recargar la página y no existe ninguna tabla,
endpoint ni persistencia real detrás. El plan (`rag_vault_plan.md` §6 Fase
2, §7.6) ya define el modelo de datos, la API y el contrato de `sources`
para esto — falta implementarlo. Persistir sesiones es también el
requisito previo de funcionalidades ya previstas para Fase 3 (memoria
conversacional, búsqueda en historial), que no tienen sentido sobre datos
que no sobreviven a un refresco de página.

## What Changes

- Nuevas tablas `chat_sessions` y `chat_messages` (SQLAlchemy,
  `backend/app/models/entities.py`), siguiendo el modelo de
  `rag_vault_plan.md` §7.6, sin el campo `collection_id` (las colecciones
  son una capability de Fase 2 aún no implementada; se añadirá en un change
  posterior cuando exista `Collection`).
- Nuevo `ChatSessionRepository` (`backend/app/repositories/chat_repo.py`,
  patrón Repository) para crear/listar/leer/eliminar sesiones y añadir
  mensajes — ninguna ruta de API accede a las tablas directamente.
- Nuevos endpoints (Facade sobre el repositorio):
  `POST /sessions`, `GET /sessions`, `GET /sessions/{id}`,
  `GET /sessions/{id}/messages`, `DELETE /sessions/{id}`.
  (`GET /sessions/search` queda fuera — es un ítem de Fase 3.)
- `POST /chat` pasa a requerir `session_id`: persiste el mensaje de usuario
  antes de invocar el pipeline y el mensaje del asistente después, con
  `sources` en el formato JSON ya documentado en `CLAUDE.md`
  (`chunks_used` + `retriever_config`) y `model_used`.
- Título de sesión auto-generado con el LLM la primera vez que se envía un
  mensaje en una sesión sin título (`TITLE_PROMPT` de
  `rag_vault_plan.md` §7.6), reutilizado tal cual sin variantes.
- El frontend (`sessionsStore`, `chatStore`) deja de usar estado mock en
  memoria y pasa a consumir la API real de sesiones: cargar el historial al
  arrancar, crear sesión real al pulsar "Nuevo chat", cargar mensajes al
  cambiar de sesión activa, y borrar sesión vía `DELETE /sessions/{id}`.
  El renombrado manual de sesiones sigue siendo solo local (no hay
  `PATCH /sessions/{id}` en el plan; se deja fuera de este change).
- **BREAKING**: `POST /chat` deja de aceptar peticiones sin `session_id`
  válido — cualquier cliente (incluida la UI) debe crear la sesión primero.

## Capabilities

### New Capabilities
- `chat-sessions`: modelo de datos, repositorio y API de sesiones y
  mensajes de chat persistidos en SQLite, con fuentes citadas guardadas
  por mensaje y título auto-generado.

### Modified Capabilities
- `rag-pipeline`: el endpoint de chat pasa de responder de forma aislada
  (sin persistencia) a requerir una sesión existente y persistir
  usuario/asistente/fuentes en ella.
- `chat-ui-shell`: el historial de sesiones y los hilos de mensajes dejan
  de ser datos mock en memoria y pasan a reflejar la API real de
  `chat-sessions` (arranque, creación, cambio de sesión activa y borrado).

## Impact

- Backend: `backend/app/models/entities.py` (tablas nuevas),
  `backend/app/repositories/chat_repo.py` (nuevo),
  `backend/app/api/routes/sessions.py` (nuevo),
  `backend/app/api/routes/chat.py` (persistencia + `session_id`),
  `backend/app/models/schemas.py` (`ChatRequest.session_id`, esquemas de
  sesión/mensaje), `backend/app/core/prompts.py` (`TITLE_PROMPT`),
  registro del router en la app FastAPI.
- Frontend: `frontend/src/stores/sessionsStore.ts`,
  `frontend/src/stores/chatStore.ts`, `frontend/src/services/api.ts`
  (nuevas llamadas a `/sessions`), `SessionList`/`SessionItem` si cambian
  los campos disponibles (p. ej. no hay `tag`/`time` con ese formato en el
  modelo de backend — se adaptan a lo que la API realmente devuelve).
- Tests: unitarios de `chat_repo.py` y de los endpoints de sesiones;
  actualizar `backend/tests/unit/test_chat_route.py` para el nuevo
  contrato con `session_id`.
- No afecta a `document_processing/`, `vector_store` ni al modelo de tags.
