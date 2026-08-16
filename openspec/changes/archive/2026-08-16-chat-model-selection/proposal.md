## Why

El selector de modelo del menú de cuenta es hoy puramente cosmético: muestra
una lista fija de nombres hardcodeados en el frontend y su valor nunca se
envía al backend, que siempre genera con `OLLAMA_MODEL` del `.env`. Un
usuario que cambia de modelo (p. ej. para pasar a uno más ligero y rápido)
no consigue ningún efecto, lo cual es confuso y le impide comparar modelos
sin editar `.env` y reiniciar el backend.

## What Changes

- El backend expone `GET /models`, que consulta el Ollama real configurado
  (`OLLAMA_BASE_URL`) y devuelve los modelos de generación realmente
  instalados (excluyendo el modelo de embeddings) junto con el modelo por
  defecto (`OLLAMA_MODEL`). Sustituye a la lista estática
  `MOCK_MODELS` del frontend.
- `POST /chat` acepta un campo `model` opcional; si se indica, se usa ese
  modelo para la generación en lugar de `OLLAMA_MODEL`. La respuesta
  (`ChatResponse`) indica qué modelo respondió.
- El modelo seleccionado en el menú de cuenta deja de ser estado local del
  componente: pasa a un store compartido (en memoria de la pestaña, sin
  persistir en `localStorage`) y se envía en cada `POST /chat` posterior a
  la selección.

## Capabilities

### New Capabilities
(ninguna)

### Modified Capabilities
- `chat-ui-shell`: el selector de modelo consulta los modelos reales de
  Ollama en vez de una lista estática, y la selección tiene efecto real
  sobre las siguientes respuestas del chat.
- `rag-pipeline`: `POST /chat` acepta un `model` opcional que sobreescribe
  `OLLAMA_MODEL` para esa petición, y `ChatResponse` indica el modelo
  usado.

## Impact

- Backend: nuevo endpoint `GET /models` (llamada real a
  `{OLLAMA_BASE_URL}/api/tags`), `ChatRequest.model` y
  `ChatResponse.model` nuevos en `models/schemas.py`,
  `core/llm_provider.get_llm()` acepta un `model` opcional.
- Frontend: `services/api.ts` gana `listModels()` real (sustituye a
  `MOCK_MODELS`) y `sendChatMessage` pasa el modelo seleccionado; nuevo
  store de Zustand para el modelo activo; `AccountMenu.tsx` y
  `chatStore.ts` se actualizan para leer/escribir ese store.
- Sin cambios de esquema de base de datos ni de infraestructura.
