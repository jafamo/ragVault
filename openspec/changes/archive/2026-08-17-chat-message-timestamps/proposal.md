## Why

Hoy el hilo de chat solo muestra la hora (`HH:MM`) de cada mensaje, nunca
la fecha, y mientras se envía o se genera una respuesta el metadato
muestra el texto fijo "ahora" en vez de una hora real. Tampoco hay forma
de saber cuánto ha tardado el modelo en responder — información útil
para comparar modelos o detectar respuestas anormalmente lentas.

## What Changes

- El metadato de cada mensaje (`Message.meta`) pasa de mostrar solo la
  hora a mostrar fecha y hora siempre (p. ej. `17/08 13:24`), tanto para
  mensajes recién enviados/generados como para los recuperados de
  `GET /sessions/{id}/messages` al recargar la página.
- Se elimina el placeholder `"ahora"`: el mensaje de usuario y el de
  asistente muestran su fecha/hora real desde el instante en que se
  crean en el store (antes de que el backend confirme nada), usando la
  hora local del cliente.
- El mensaje del asistente muestra, junto al modelo y la hora, cuánto ha
  tardado en completarse la respuesta (p. ej.
  `qwen2.5:14b · 17/08 13:24 · 3.2s`), medido desde que el usuario envía
  la pregunta hasta que el stream SSE termina (evento `done`) — incluye
  la recuperación de documentos y todo el streaming, no solo la
  generación de texto.
- La duración solo aparece una vez la respuesta está completa; mientras
  el mensaje sigue en streaming no se muestra un cronómetro en vivo.
- Al recargar la página y recuperar mensajes ya persistidos, la duración
  se recalcula a partir de los `created_at` reales del mensaje de
  usuario y su respuesta (misma sesión, turno consecutivo), no de nada
  medido en el cliente en ese momento.

## Capabilities

### New Capabilities

(ninguna)

### Modified Capabilities

- `rag-pipeline`: el requirement "Chat de la UI conectada al pipeline
  real" se amplía para especificar el formato de fecha/hora y la
  duración mostrada en los mensajes del hilo.

## Impact

- Frontend: `frontend/src/stores/chatStore.ts` (`formatTime` →
  formato con fecha, cálculo de duración en `sendMessage` y en
  `fromApiMessage`, eliminar placeholders `"ahora"`),
  `frontend/src/components/Chat/MessageBubble.tsx` (sin cambios de
  lógica, ya renderiza `message.meta` tal cual).
- Sin cambios de backend: no se persiste la duración ni se añade ningún
  campo nuevo a `ChatMessage` — se deriva siempre de `created_at` (ya
  persistido) o de marcas de tiempo locales del cliente mientras la
  sesión sigue abierta.
