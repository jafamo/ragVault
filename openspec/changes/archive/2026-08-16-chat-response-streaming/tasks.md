## 1. Pipeline: paso de generación en streaming

- [x] 1.1 Añadir `make_generate_step_stream(llm)` en
      `backend/app/core/rag_pipeline.py`: async generator que envuelve
      `llm.astream(ctx["prompt"])` y va cediendo cada chunk de texto, sin
      tocar `make_generate_step` existente (sigue usándolo
      `generate_title`).
- [x] 1.2 Reutilizar los pasos previos del pipeline (recuperación,
      construcción de prompt) sin cambios delante del nuevo paso streaming.
- [x] 1.3 Tests unitarios del nuevo paso: dado un `llm` fake que emite
      varios chunks vía `astream`, verificar que el generador cede cada
      chunk en orden y que la concatenación final coincide con la
      respuesta completa.

## 2. Backend: endpoint SSE

- [x] 2.1 Cambiar `POST /chat` en `backend/app/api/routes/chat.py` para
      validar `session_id` (existente) y devolver un error 4xx *antes* de
      abrir el stream si la sesión no existe, igual que hoy. Quitar
      `response_model=ChatResponse` del decorador de la ruta (incompatible
      con `StreamingResponse`).
- [x] 2.2 Ejecutar el paso de recuperación (`make_retrieve_step`) *fuera*
      del generador, antes de abrir el stream: si falla (p. ej. ChromaDB
      no disponible), responder con un 5xx normal sin llegar a abrir SSE.
      Si `retrieved` está vacío, seguir tratándolo como caso
      "sin documentos" (no error), resuelto dentro del stream con
      `NO_DOCUMENTS_ANSWER` como único chunk.
- [x] 2.3 Persistir el mensaje de usuario antes de empezar a generar
      (como hoy), luego devolver `StreamingResponse` con
      `media_type="text/event-stream"` y headers `Cache-Control: no-cache`
      y `X-Accel-Buffering: no`.
- [x] 2.4 Implementar el async generator de la respuesta: por cada chunk
      de `make_generate_step_stream`, emitir un frame SSE
      `event: chunk\ndata: <json.dumps(texto)>\n\n` (el texto va
      serializado como JSON, no como texto plano, para que los saltos de
      línea del propio chunk no rompan el framing SSE), acumulando el
      texto completo en memoria para persistencia posterior.
- [x] 2.5 Comprobar `await request.is_disconnected()` en cada iteración
      del generador; si el cliente se desconectó, cortar el bucle sin
      seguir consumiendo tokens de Ollama y sin persistir nada del
      asistente.
- [x] 2.6 Al agotarse el stream de Ollama con éxito: persistir el mensaje
      de asistente (texto acumulado + `sources` con el formato
      `{"chunks_used": [...], "retriever_config": {...}}` ya definido en
      `chat-sessions`) y emitir `event: done\ndata:
      <json.dumps({"sources": [...], "model": "..."})>\n\n`. Después de
      emitir `done` (no antes), invocar `_try_generate_title` igual que
      hoy si la sesión no tiene título todavía, para no retrasar la
      aparición de la respuesta ni de las fuentes.
- [x] 2.7 Envolver la generación en `try/except`: si Ollama falla a mitad
      de stream, emitir `event: error\ndata:
      <json.dumps({"message": "..."})>\n\n`, cerrar el stream sin
      persistir respuesta de asistente parcial.
- [x] 2.8 Actualizar/crear tests de integración del endpoint usando
      `httpx.AsyncClient`/`ASGITransport` (el `TestClient` síncrono no
      sirve para consumir un `StreamingResponse` progresivamente) y
      verificar: secuencia de eventos `chunk`* + `done`, persistencia del
      turno completo, fallo de recuperación devolviendo 5xx sin abrir
      stream, y error mid-stream sin persistencia parcial. Incluir un caso
      con un chunk que contenga un salto de línea para probar el escapado
      JSON del framing.

## 3. Frontend: consumo del stream

- [x] 3.1 Reescribir `sendChatMessage` en `frontend/src/services/api.ts`
      para hacer `fetch(POST /chat)` con un `AbortSignal` opcional, y
      devolver un iterador/callback sobre `response.body.getReader()` en
      vez de `res.json()`, decodificando con `TextDecoder` en modo
      `{stream: true}` (no un decode nuevo por lectura, para no cortar
      caracteres UTF-8 multibyte a la mitad) y parseando frames
      `event:`/`data:` separados por línea en blanco, con `JSON.parse`
      sobre el contenido de `data:`.
- [x] 3.2 Actualizar `frontend/src/stores/chatStore.ts` (línea ~99) para
      consumir el nuevo `sendChatMessage`: crear el mensaje de asistente
      vacío al primer `chunk`, ir concatenando texto en el store con cada
      `chunk` recibido, y fijar `sources`/`model` al recibir `done`.
      Mantener `pendingSessionId` fijado durante todo el stream (no solo
      hasta el primer chunk), para que el input siga deshabilitado hasta
      `done`/`error`.
- [x] 3.3 Manejar el evento `error` en el store: marcar el mensaje del
      asistente en curso con un estado de error visible, sin tratarlo como
      respuesta completa.
- [x] 3.4 Añadir un `AbortController` por envío: abortar el `fetch` en
      curso si el usuario cambia de sesión activa o el componente de chat
      se desmonta antes de que el stream termine, para no seguir
      escribiendo chunks en el store de una sesión que ya no está visible.
- [x] 3.5 Verificar que `ChatWindow.tsx`/`MessageBubble.tsx` re-renderizan
      correctamente con las actualizaciones incrementales de contenido
      (sin flicker ni scroll saltando de forma extraña con cada chunk).
- [x] 3.6 Verificar que `SourcesCited` sigue mostrando las fuentes igual
      que antes, ahora alimentado por el evento `done` en vez del JSON
      completo original.

## 4. Verificación manual y revisión

- [x] 4.1 Probar en la app real (`/run`): pregunta con documentos
      indexados y ver el texto aparecer incrementalmente; pregunta sin
      documentos indexados; cambio de pestaña/cierre a mitad de respuesta
      para comprobar que el backend corta la generación.
- [x] 4.2 Ejecutar la skill `ragvault-pattern-review` sobre el diff antes
      de `git flow feature finish`.
- [x] 4.3 Añadir entrada en `CHANGELOG.md` bajo `[Sin publicar]` (`Changed`)
      describiendo que las respuestas del chat ahora aparecen en streaming,
      referenciando el change `chat-response-streaming`.
