## Why

El chat actual responde de golpe: `POST /chat` espera a que el LLM termine
de generar toda la respuesta antes de devolver nada, y la UI se queda en
estado de carga hasta recibir el JSON completo. Esto da una sensación de
lentitud (respuestas largas tardan varios segundos sin ningún feedback
incremental) y desaprovecha que `ChatOllama` ya soporta streaming
(`.stream()`/`.astream()`) en LangChain. Pasar a streaming vía SSE mejora
la percepción de latencia sin cambiar el modelo ni el pipeline de
recuperación.

## What Changes

- El endpoint `POST /chat` pasa de devolver un único JSON `ChatResponse` a
  responder con `text/event-stream` (SSE), emitiendo eventos incrementales
  con los tokens/chunks de la respuesta a medida que el LLM los genera.
  **BREAKING**: cambia el contrato HTTP de `POST /chat` (deja de ser
  `application/json` de una sola pieza).
- El paso de generación del pipeline RAG (`make_generate_step` en
  `rag_pipeline.py`) gana una variante que consume `llm.astream(...)` en
  vez de `llm.invoke(...)`, cediendo cada chunk al llamador en vez de
  devolver la respuesta completa de una vez.
- Las fuentes citadas (`sources`) y el `model` usado, que hoy viajan en el
  mismo JSON que la respuesta, se emiten como el evento final del stream
  SSE (una vez generado el texto completo), para no romper el contrato de
  persistencia de `ChatMessage.sources` ya establecido.
- El frontend (`api.ts`, `chatStore.ts`, `ChatWindow`/`MessageBubble`) deja
  de hacer `fetch(...).json()` y pasa a consumir el stream SSE,
  actualizando el contenido del mensaje del asistente incrementalmente en
  el store a medida que llegan chunks, y fijando fuentes/modelo al recibir
  el evento final.
- La generación del título de sesión (`generate_title`) sigue usando
  `llm.invoke(...)` sin cambios: no es contenido que el usuario vea
  aparecer en streaming.
- La persistencia del turno en base de datos (mensaje de usuario +
  respuesta de asistente con `sources`) sigue ocurriendo una vez completado
  el stream, dentro de la misma petición — no cambia el contrato ya
  definido en `chat-sessions`.

## Capabilities

### New Capabilities

(ninguna — este change modifica el comportamiento de streaming de una
capability ya existente en vez de introducir una nueva)

### Modified Capabilities

- `rag-pipeline`: el requirement "Endpoint de chat con fuentes citadas"
  cambia de una respuesta JSON única a una respuesta SSE incremental
  (nuevos escenarios de streaming, evento final con fuentes/modelo,
  manejo de errores a mitad de stream); el requirement "Chat de la UI
  conectada al pipeline real" cambia para reflejar que la UI renderiza la
  respuesta token a token en vez de esperar el JSON completo.

## Impact

- Backend: `backend/app/api/routes/chat.py` (respuesta `StreamingResponse`
  SSE en vez de `ChatResponse` directo), `backend/app/core/rag_pipeline.py`
  (`make_generate_step` con variante streaming sobre `llm.astream(...)`),
  persistencia de `ChatMessage` sin cambios de esquema.
- Frontend: `frontend/src/services/api.ts` (`sendChatMessage` pasa a
  consumir un `ReadableStream`/`EventSource`-like en vez de `res.json()`),
  `frontend/src/stores/chatStore.ts` (actualización incremental del
  mensaje del asistente en el estado), `frontend/src/components/Chat/`
  (`ChatWindow.tsx`, `MessageBubble.tsx` re-renderizan con cada chunk).
- Sin cambios de esquema de base de datos ni de dependencias nuevas
  (SSE se implementa con las capacidades ya presentes de FastAPI/Starlette
  `StreamingResponse` y `fetch`/`ReadableStream` nativo del navegador).
