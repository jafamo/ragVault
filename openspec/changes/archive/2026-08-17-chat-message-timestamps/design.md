## Context

`frontend/src/stores/chatStore.ts` tiene hoy `formatTime(iso)` que solo
extrae `HH:MM` vía `toLocaleTimeString`, usado tanto en `fromApiMessage`
(mensajes recargados desde `GET /sessions/{id}/messages`, con `created_at`
real del backend) como al construir los mensajes optimistas en
`sendMessage`, donde en vez de una hora real se usa el literal `"ahora"`
hasta que llega la respuesta — momento en el que el mensaje de usuario
tampoco se actualiza (se queda con `"ahora"` para siempre hasta recargar
la página).

No existe ningún campo de duración ni en el modelo `Message` del store ni
en `ChatMessage` del backend; hay que decidir cómo derivarla sin tocar el
contrato persistido.

## Goals / Non-Goals

**Goals:**
- Todo mensaje (usuario o asistente) muestra fecha + hora real desde el
  momento en que aparece en el store, tanto recién creado como recargado.
- El mensaje de asistente muestra la duración total de la respuesta
  (envío → evento `done`) una vez completada.
- La duración se calcula igual en ambos casos — sesión activa en curso y
  sesión recargada desde el backend — para que no cambie al refrescar la
  página.

**Non-Goals:**
- No se añade un cronómetro en vivo mientras la respuesta se está
  generando (decidido explícitamente por el usuario).
- No se persiste la duración como campo nuevo en `ChatMessage` ni se
  añade al payload del evento `done` de SSE — se deriva siempre de
  timestamps ya disponibles.
- No se cambia el formato de fecha/hora en ningún otro punto de la UI
  (panel HISTORIAL, vista previa de sesión) — solo en el hilo de chat.

## Decisions

### Formato de fecha/hora: `dd/mm HH:mm`, sin año
Se sustituye `formatTime` por `formatDateTime(iso)`, usando
`toLocaleDateString`/`toLocaleTimeString` (o `Intl.DateTimeFormat`)
en locale `es-ES` con día y mes de 2 dígitos y hora `HH:mm`, sin año —
el historial de sesiones de esta app no se espera que abarque varios
años, y añadir el año sería ruido visual constante. Ejemplo:
`17/08 13:24`.

### Duración derivada de dos timestamps, no de un campo nuevo
La duración de una respuesta se calcula como
`assistantTimestamp - userTimestamp` de ese turno, en vez de crear un
campo `duration_ms` persistido:
- **Sesión activa (streaming en curso)**: `sendMessage` captura
  `const sentAt = Date.now()` al construir el mensaje de usuario, y al
  recibir el evento `done` calcula `Date.now() - sentAt`. No requiere
  cambios en el payload SSE.
- **Sesión recargada** (`fromApiMessage` sobre
  `GET /sessions/{id}/messages`): se calcula
  `new Date(assistantMsg.created_at).getTime() -
  new Date(userMsg.created_at).getTime()` entre el mensaje de asistente
  y el mensaje de usuario inmediatamente anterior en la lista ya
  ordenada cronológicamente que devuelve el endpoint.

Alternativa descartada: añadir `elapsed_ms` al evento `done` de SSE y/o
a `ChatMessage.sources` persistido. Se descarta porque duplicaría la
misma información que ya se puede derivar de `created_at`, y complicaría
el contrato de streaming ya cerrado en `chat-response-streaming` sin
necesidad real.

### Timestamps reales desde la creación optimista, sin placeholder
Los mensajes optimistas creados en `sendMessage` (antes de que el
backend confirme nada) usan `new Date().toISOString()` real en vez del
literal `"ahora"`, formateado con `formatDateTime` igual que los
recargados — así el usuario ve la hora real de inmediato y no hace falta
"arreglar" el metadato del mensaje de usuario más tarde.

### La duración solo se fija al completar, no se re-renderiza en vivo
Mientras `message.streaming` es `true`, el metadato del asistente
muestra solo modelo + hora (sin duración); al llegar `done`, se añade el
tramo `· Ns` al `meta` en la misma actualización que ya fija `sources`.
No hay `setInterval` ni recomputo periódico — coherente con el Non-Goal
de no mostrar un cronómetro en vivo.

### Formato de la duración: segundos con un decimal
`(ms / 1000).toFixed(1) + "s"` — suficiente precisión para distinguir
respuestas rápidas de lentas sin la complejidad de un formato `mm:ss`
para respuestas de RAG, que en la práctica rara vez superan 1-2 minutos;
si en el futuro se observan respuestas mucho más largas, se puede
revisar en un change posterior.

### Parseo de `created_at` como UTC explícito (descubierto durante la implementación)
El backend serializa `created_at` como ISO sin sufijo de timezone (p. ej.
`2026-08-16T14:02:42.416105`, sin `Z` ni offset) — naive pero en UTC.
`new Date(iso)` en el navegador interpreta un ISO sin timezone como hora
**local**, no UTC, así que los mensajes recargados desde
`GET /sessions/{id}/messages` se mostraban desplazados por el offset
local (2h en verano en España), aunque los mensajes recién enviados (con
`Date.now()` del cliente) se veían correctos — este desajuste solo se
hacía evidente al comparar el antes/después de recargar la página, que
es justo lo que exige el Scenario "Duración recalculada al recargar la
página". Se añade `parseUtcIso(iso)` en `chatStore.ts`, que añade `Z` al
string si no trae ya marca de timezone, y se usa en vez de `new
Date(iso)` en `formatDateTime` y en el cálculo de duración de
`fromApiMessage`. Es un bug preexistente (afectaba ya a `formatTime`
antes de este change) que se corrige aquí porque el propio requirement
de esta feature lo hace visible e incorrecto; no se ha tocado
`formatRelativeTime` de `SessionItem.tsx` (mismo bug, pero fuera del
alcance de este change) — queda como candidato a un fix futuro si se
observa que afecta al panel HISTORIAL de forma perceptible.

## Risks / Trade-offs

- **[Riesgo]** El reloj del cliente puede estar ligeramente desincronizado
  del servidor, así que la duración "en vivo" (sesión activa) y la
  recalculada tras recargar (basada en `created_at` del servidor) pueden
  diferir en un margen pequeño → **Mitigación**: diferencia esperada del
  orden de milisegundos/segundos, irrelevante para el propósito de esta
  feature (percepción aproximada de velocidad, no medición exacta).
- **[Trade-off]** Si el usuario recarga la página a mitad de una
  respuesta en streaming, el mensaje parcial se pierde (comportamiento ya
  existente, sin cambios) — la duración de ese turno nunca se calcula
  porque no llegó a persistirse el mensaje de asistente.

## Migration Plan

Sin migración de datos ni cambios de backend. Cambio de frontend puro.

## Open Questions

Ninguna pendiente.
