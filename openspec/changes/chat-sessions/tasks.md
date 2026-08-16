## 1. Backend: modelo de datos

- [x] 1.1 Añadir `ChatSession` y `ChatMessage` a `backend/app/models/entities.py` siguiendo `rag_vault_plan.md` §7.6, sin `collection_id` (ver Non-Goals de `design.md`): `ChatSession(id, title: str | None, created_at, updated_at)`, `ChatMessage(id, session_id FK, role, content, created_at, model_used: str | None, sources: str | None)`, relación 1:N con `cascade="all, delete-orphan"`.
- [x] 1.2 Añadir `ChatRequest.session_id: str`, y esquemas Pydantic `SessionResponse` (`id`, `title`, `created_at`, `updated_at`) y `MessageResponse` (`id`, `role`, `content`, `created_at`, `model_used`, `sources`) en `backend/app/models/schemas.py`.

## 2. Backend: repositorio

- [x] 2.1 Crear `backend/app/repositories/chat_repo.py` con `ChatSessionRepository`, reutilizando `_SessionLocal` de `document_repo.py` (mismo patrón que `tag_repo.py`/`stats_repo.py`). Nota: `create_all` no se llama por-repo — se sigue el patrón real ya existente (`init_db()` en el `lifespan` de `main.py`, no en `__init__`), que `ChatSession`/`ChatMessage` heredan automáticamente al compartir `Base`.
- [x] 2.2 Implementar `create_session() -> ChatSession`, `list_sessions() -> list[ChatSession]` (orden `updated_at` desc), `get_session(id) -> ChatSession | None`, `delete_session(id) -> bool`.
- [x] 2.3 Implementar `add_message(session_id, role, content, model_used=None, sources=None) -> ChatMessage`, actualizando `session.updated_at`; `list_messages(session_id) -> list[ChatMessage]` en orden cronológico.
- [x] 2.4 Implementar `set_title_if_empty(session_id, title) -> None`, no-op si la sesión ya tiene título (evita condiciones de carrera triviales entre mensajes).

## 3. Backend: endpoints de sesiones

- [x] 3.1 Crear `backend/app/api/routes/sessions.py`: `POST /sessions`, `GET /sessions`, `GET /sessions/{id}` (404 si no existe), `GET /sessions/{id}/messages` (404 si la sesión no existe), `DELETE /sessions/{id}` (404 si no existe) — como Facade sobre `ChatSessionRepository`, sin lógica de negocio adicional.
- [x] 3.2 Registrar el nuevo router en la app FastAPI (junto a los routers existentes de chat/documents/tags/stats).

## 4. Backend: persistencia en `/chat` y auto-título

- [x] 4.1 Añadir `TITLE_PROMPT` a `backend/app/core/prompts.py` (texto literal de `rag_vault_plan.md` §7.6).
- [x] 4.2 Modificar `POST /chat` (`backend/app/api/routes/chat.py`): validar `session_id` contra `ChatSessionRepository.get_session` (404/400 si no existe); persistir el mensaje de usuario antes de invocar `run_pipeline`; tras la respuesta, persistir el mensaje de asistente con `sources` serializado como `{"chunks_used": [...], "retriever_config": {"top_k": ..., "filter_tags": []}}` y `model_used=model`.
- [x] 4.3 Si la sesión no tiene título y el mensaje persistido es el primero de esa sesión, invocar el LLM con `TITLE_PROMPT` y `set_title_if_empty`; envolver en try/except para que un fallo en la generación de título no interrumpa la respuesta del chat.

## 5. Backend: tests

- [x] 5.1 Tests unitarios de `chat_repo.py`: crear/listar/leer/eliminar sesión, cascade al borrar, `add_message`/`list_messages`, `set_title_if_empty` no sobrescribe título existente.
- [x] 5.2 Tests de los endpoints de `sessions.py`: crear+listar, 404 en sesión inexistente, borrado en cascada.
- [x] 5.3 Actualizar `backend/tests/unit/test_chat_route.py` para incluir `session_id` en las peticiones existentes y añadir casos: `session_id` ausente/inválido → 4xx sin persistir nada; turno completo persistido tras `POST /chat` exitoso; auto-título generado en el primer mensaje y no regenerado en el segundo.

## 6. Frontend: API client

- [x] 6.1 Añadir a `frontend/src/services/api.ts`: `listSessions()`, `createSession()`, `getSessionMessages(id)`, `deleteSession(id)`, tipadas contra los esquemas nuevos del backend.
- [x] 6.2 Añadir `session_id` al body de `sendChatMessage` (`frontend/src/services/api.ts`) y a su firma.

## 7. Frontend: stores

- [x] 7.1 Reescribir `sessionsStore.ts` para cargar sesiones reales al arrancar (`listSessions`), `createSession` como llamada async a `POST /sessions` (manteniendo la comprobación de "sesión activa vacía" antes de llamar), `deleteSession` como llamada async a `DELETE /sessions/{id}` (con la misma garantía de "nunca sin sesión activa" creando una nueva si borra la última). `renameSession` sigue siendo solo estado local (no hay endpoint de renombrado).
- [x] 7.2 Adaptar el tipo `Session` del frontend: eliminar `tag` (no existe en el modelo de backend); derivar `time`/fecha relativa a partir de `updated_at` en el componente en vez de guardarlo como campo de estado.
- [x] 7.3 Reescribir `chatStore.ts` para cargar mensajes de una sesión bajo demanda (`getSessionMessages`) al activarla en vez de mantener `initialMessages` en memoria; `sendMessage` pasa a incluir `session_id` en la llamada a `sendChatMessage` y usa la respuesta persistida por el backend en vez de construir el mensaje de asistente solo en cliente.

## 8. Frontend: UI

- [x] 8.1 Adaptar `SessionItem.tsx` a los campos disponibles tras 7.2 (sin `tag`; `time` formateado desde `updated_at`), verificando ambas identidades visuales (Ledger/Terminal) y el modo colapsado.
- [x] 8.2 Verificar manualmente en navegador: crear sesión, enviar mensaje, recargar la página y confirmar que la sesión y el mensaje siguen ahí; borrar sesión y confirmar que desaparece tras recargar.

## 9. Verificación final

- [x] 9.1 Ejecutar la suite de tests de backend y el type-check de frontend.
- [x] 9.2 Ejecutar `ragvault-pattern-review` sobre el diff antes de `git flow feature finish`.
