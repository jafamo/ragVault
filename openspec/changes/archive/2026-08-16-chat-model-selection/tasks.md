## 1. Backend — listar modelos reales

- [x] 1.1 Añadir `GET /models` (nueva ruta o en `chat.py`) que llama a
      `{OLLAMA_BASE_URL}/api/tags`, excluye `settings.ollama_embed_model`
      de la lista y devuelve también `default` (`settings.ollama_model`)
- [x] 1.2 Manejar el caso de Ollama no disponible con un error controlado
      (mismo patrón que `GET /health`), sin excepción no controlada

## 2. Backend — modelo por petición en /chat

- [x] 2.1 Añadir `model: str | None = None` a `ChatRequest` y `model: str`
      a `ChatResponse` en `models/schemas.py`
- [x] 2.2 `core/llm_provider.get_llm()` acepta `model: str | None = None`
      y usa `settings.ollama_model` como fallback
- [x] 2.3 `api/routes/chat.py` pasa `request.model` a `get_llm()` y
      devuelve el modelo efectivamente usado en `ChatResponse.model`

## 3. Frontend — modelo compartido entre menú y chat

- [x] 3.1 `services/api.ts`: `listModels()` llama a `GET /models` (con
      fallback a un único modelo si la llamada falla) en vez de devolver
      `MOCK_MODELS`; `sendChatMessage` acepta y envía `model`
- [x] 3.2 Nuevo store de Zustand (`modelStore`) con el modelo activo,
      inicializado tras la respuesta de `GET /models`, sin persistencia
      en `localStorage`
- [x] 3.3 `AccountMenu.tsx` lee/escribe `modelStore` en vez de `useState`
      local para el selector
- [x] 3.4 `chatStore.sendMessage` lee el modelo activo del store y lo
      envía en cada `sendChatMessage`; el meta del mensaje de respuesta
      muestra el modelo que realmente contestó (`ChatResponse.model`)

## 4. Verificación

- [x] 4.1 Tests backend: `GET /models` (éxito y Ollama caído), `POST
      /chat` con y sin `model` explícito
- [x] 4.2 Ejecutar `ragvault-pattern-review` sobre el diff antes de
      `git flow feature finish`
- [x] 4.3 Probar manualmente: cambiar de modelo en el selector, enviar un
      mensaje, confirmar que el meta de la respuesta refleja el modelo
      elegido (no el de `.env`), y que recargar la página vuelve al
      modelo por defecto
