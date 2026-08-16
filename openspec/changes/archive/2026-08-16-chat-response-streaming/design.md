## Context

`POST /chat` (`backend/app/api/routes/chat.py:34-67`) ejecuta hoy
`run_pipeline(...)` de forma síncrona y devuelve un único `ChatResponse`
JSON. El paso de generación (`make_generate_step` en
`backend/app/core/rag_pipeline.py:49-55`) llama a `llm.invoke(ctx["prompt"])`
de forma bloqueante. El cliente LLM (`ChatOllama`, vía
`backend/app/core/llm_provider.py`) ya soporta `.astream(...)` de LangChain,
así que no hace falta cambiar de librería ni de modelo — solo la forma en
que se consume la respuesta.

El frontend (`frontend/src/services/api.ts:139-152`,
`frontend/src/stores/chatStore.ts:99-103`) hace hoy un `fetch(...).json()`
simple y escribe el mensaje completo del asistente de una vez en el store.

Este es un cambio transversal (backend + frontend, contrato HTTP nuevo)
que justifica documentar decisiones antes de implementar.

## Goals / Non-Goals

**Goals:**
- El texto de la respuesta del asistente llega al frontend en chunks
  incrementales, visibles a medida que el LLM los genera.
- Las fuentes citadas y el modelo usado siguen viajando en la misma
  petición, disponibles al final del stream.
- El turno completo (mensaje de usuario + respuesta de asistente con
  fuentes) se sigue persistiendo en la misma petición HTTP, sin introducir
  un segundo endpoint ni un job asíncrono separado.
- Errores del LLM a mitad de generación se comunican explícitamente al
  cliente en vez de cortar la conexión en silencio.

**Non-Goals:**
- No se implementa cancelación de generación desde el cliente (detener el
  stream a mitad de respuesta) — se puede añadir en un change posterior.
- No se hace streaming de la generación de título de sesión
  (`generate_title`) — sigue siendo una llamada bloqueante, ya que el
  usuario no espera visualmente ese texto.
- No se implementa reconexión/resume de stream (`Last-Event-ID`) — si la
  conexión se corta, el cliente reintenta la pregunta desde cero.
- No cambia el modelo de datos de `ChatMessage` ni el formato ya definido
  de `sources` (`chunks_used`/`retriever_config`).

## Decisions

### Formato de eventos SSE
Se usan eventos con `event:` nombrado en vez de solo `data:` sin tipo, para
que el cliente distinga sin ambigüedad los tres tipos de mensaje:
- `event: chunk` — `data` es un fragmento de texto plano de la respuesta.
- `event: done` — `data` es un JSON `{"sources": [...], "model": "..."}`,
  se emite una única vez al terminar la generación con éxito.
- `event: error` — `data` es un JSON `{"message": "..."}`, se emite si el
  LLM falla a mitad de generación; el stream se cierra después.

Alternativa descartada: eventos solo `data:` con un campo `type` embebido
en el JSON. Se prefiere `event:` nombrado porque es el mecanismo estándar
de SSE y simplifica el parseo en el cliente (switch por `event.type` del
`EventSource`-like reader).

### Transporte: `fetch` + `ReadableStream`, no `EventSource`
El navegador soporta `EventSource` nativo para SSE, pero solo permite
peticiones `GET` sin cuerpo. Como `POST /chat` necesita enviar
`{question, session_id, model}` en el body, el cliente consume el stream
leyendo `response.body.getReader()` sobre el `fetch` POST y parseando
manualmente los frames `event:`/`data:` separados por línea en blanco. El
decodificado de bytes a texto usa `TextDecoder` en modo `{stream: true}`
(no un decode nuevo por chunk), porque un carácter UTF-8 multibyte puede
quedar partido entre dos lecturas del `reader`.

### Escapado de texto multilínea en `data:`

El texto que genera el LLM puede contener saltos de línea, y el framing
SSE trata una línea en blanco como fin de evento — un `data: <texto con
\n>\n\n` ingenuo corrompería el stream. Cada chunk se serializa como JSON
(`data: "texto con \n escapado"\n\n` vía `json.dumps`) en vez de texto
plano sin escapar, tanto para `chunk` como para `done`/`error`; el cliente
hace `JSON.parse` del contenido de cada `data:` antes de usarlo.

### `response_model` se retira de la ruta

`POST /chat` deja de declarar `response_model=ChatResponse` en el
decorador de FastAPI: con `StreamingResponse` no hay un cuerpo JSON único
que validar contra ese modelo, y dejarlo declarado haría que FastAPI
intente validar la respuesta incorrectamente. `ChatResponse` como
`BaseModel` puede seguir existiendo para describir la forma del payload
del evento `done`, pero sin usarse como `response_model`.

### Orden: recuperación fuera del generador, generación dentro

El paso de recuperación (`make_retrieve_step`, contra ChromaDB) se ejecuta
**antes** de abrir el `StreamingResponse`, igual que hoy se ejecuta antes
de tener respuesta del LLM. Si la recuperación falla (p. ej. ChromaDB no
disponible), la ruta responde con un error 5xx normal, sin llegar a abrir
el stream — el cliente lo trata como cualquier fallo de `fetch` antes de
tener `response.ok`. Solo la generación (`llm.astream(...)`) ocurre dentro
del async generator del stream, porque es la única parte que necesita
emitir progreso incremental. El caso "sin documentos indexados" (lista de
`retrieved` vacía) sigue sin ser un error: se resuelve devolviendo
`NO_DOCUMENTS_ANSWER` igual que hoy, pero ahora como un stream de un solo
chunk seguido de `done` con `sources: []`.

### Generación de título después del evento `done`

`_try_generate_title` se sigue invocando de forma síncrona y bloqueante
(sin cambios en `generate_title`), pero se llama **después** de emitir el
evento `done` y antes de cerrar el generador — así no retrasa la
aparición del primer chunk de texto ni el momento en que el usuario ve la
respuesta completa. El pequeño retraso adicional en cerrar la conexión
HTTP (invisible para el usuario, que ya ve la respuesta y las fuentes) es
aceptable frente a la alternativa de paralelizarlo con un task en
background, que complicaría el manejo de errores sin necesidad.

### Cancelación de la lectura en el cliente

El `fetch` del stream se lanza con un `AbortController`; su señal se aborta
si el usuario cambia de sesión activa o el componente de chat se
desmonta mientras el stream sigue en curso, para no seguir escribiendo
chunks en el store de una sesión que ya no está en pantalla ni mantener
la conexión abierta innecesariamente.

### Persistencia: al final del stream, dentro de la misma request
El mensaje de usuario se persiste antes de empezar a generar (igual que
hoy). El mensaje de asistente (con `sources`) se persiste **después** de
que el generador interno acumule el texto completo, justo antes de emitir
el evento `done` — el generador de FastAPI (`StreamingResponse` sobre un
async generator) hace ambas cosas: yield de chunks al cliente y, al
agotarse el stream de `llm.astream(...)`, escribe en base de datos.

Si el LLM falla a mitad de generación, **no** se persiste el mensaje de
asistente (queda solo el mensaje de usuario, igual que si la petición
hubiera fallado antes del streaming) — evita mensajes de asistente
truncados y silenciosamente incompletos en el historial.

### `make_generate_step` gana una variante streaming
Se añade una función `make_generate_step_stream(llm)` que devuelve un
async generator sobre `llm.astream(ctx["prompt"])`, en vez de modificar
`make_generate_step` existente — el pipeline no-streaming (usado por
`generate_title` y por tests que no necesitan streaming) se mantiene
intacto. Ambas comparten la construcción del prompt (paso anterior del
pipeline, sin cambios).

### Headers para evitar buffering intermedio
La respuesta SSE incluye `Cache-Control: no-cache`,
`X-Accel-Buffering: no` (por si en el futuro hay un proxy nginx delante) y
`Content-Type: text/event-stream`, para que ni el navegador ni un posible
proxy acumulen chunks antes de entregarlos.

## Risks / Trade-offs

- **[Riesgo]** Un proxy intermedio (no presente hoy, pero posible en
  producción) podría bufferizar la respuesta SSE pese a los headers →
  **Mitigación**: documentar en el design que cualquier proxy añadido en
  el futuro debe desactivar buffering explícitamente para esta ruta.
- **[Riesgo]** El contrato de `POST /chat` cambia de forma incompatible
  (JSON → SSE) → **Mitigación**: backend y frontend se despliegan juntos
  en el mismo change; no hay consumidores externos documentados de este
  endpoint fuera de la UI propia.
- **[Riesgo]** Si el cliente cierra la pestaña o navega fuera a mitad de
  stream, el generador seguiría consumiendo tokens de Ollama sin nadie
  escuchando → **Mitigación**: comprobar `request.is_disconnected()` en
  cada iteración del generador y cortar la llamada a Ollama si el cliente
  ya no está conectado.
- **[Trade-off]** No hay cancelación explícita desde el cliente (Non-Goal)
  — el usuario no puede "parar" una respuesta larga; se acepta como
  limitación de este change.

## Migration Plan

No hay migración de datos (sin cambios de esquema). El despliegue es
atómico: se fusiona `feature/chat-response-streaming` con backend y
frontend juntos, ya que el contrato HTTP es incompatible entre versiones.
Rollback: revertir el merge completo (backend + frontend a la vez); no es
seguro desplegar solo uno de los dos lados.

## Open Questions

Ninguna pendiente — las decisiones de formato de evento, persistencia y
manejo de errores mid-stream quedan fijadas arriba.
