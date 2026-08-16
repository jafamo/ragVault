## Why

El chat solo tiene una sesión activa fija (`s5`, la primera de la lista de
ejemplo) y no existe ninguna forma de empezar una conversación en blanco:
para cambiar de tema el usuario tiene que reutilizar el hilo de una sesión
existente, mezclando preguntas sin relación en el mismo historial de
mensajes. Se necesita un botón de "nuevo chat" que cree una sesión vacía y
la active, para poder abrir un tema o pregunta distinta sin arrastrar el
contexto de la conversación anterior.

Además, el historial (`s1`-`s5`) y sus mensajes de ejemplo son datos mock
hardcodeados que no corresponden a conversaciones reales del usuario;
mostrarlos en el frontend es confuso ahora que va a existir un flujo real
para crear sesiones, y conviene retirarlos de la vista en el mismo change
en vez de dejarlos conviviendo con sesiones reales.

## What Changes

- Añadir un botón "Nuevo chat" visible en el panel de historial
  (`SessionList`), tanto en su estado expandido como en el colapsado
  (icono-only, igual que el resto de controles del panel colapsado).
- Al pulsarlo, `sessionsStore` crea una sesión nueva (id único, título por
  defecto tipo "Nueva conversación", sin tag, marcada como "ahora"), la
  inserta al principio de la lista y la marca como activa.
- `chatStore` debe reflejar la sesión nueva con un hilo de mensajes vacío
  (sin heredar mensajes de la sesión anterior) y sin disparar ninguna
  llamada a `POST /chat` hasta que el usuario escriba el primer mensaje.
- Si el usuario pulsa "Nuevo chat" estando ya en una sesión vacía sin
  mensajes, no se crea una sesión duplicada: se reutiliza la sesión activa
  vacía tal cual.
- Retirar del frontend los datos mock del historial (`initialSessions` en
  `sessionsStore` e `initialMessages` en `chatStore`, sesiones `s1`-`s5`):
  la aplicación arranca con el historial vacío salvo por una sesión nueva
  creada automáticamente con la misma lógica de "Nuevo chat", en vez de
  mostrar conversaciones de ejemplo hardcodeadas.
- Sin cambios de backend: las sesiones siguen siendo estado en memoria del
  frontend (no hay persistencia ni tabla de sesiones todavía — eso es
  trabajo de una capability `chat-sessions` futura descrita en el plan).

## Capabilities

### New Capabilities
(ninguna)

### Modified Capabilities
- `chat-ui-shell`: se añade el requisito de poder iniciar una sesión de
  chat nueva y vacía desde el panel de historial, y se aclara que el hilo
  de mensajes de cada sesión es independiente del de las demás.

## Impact

- Frontend: `frontend/src/stores/sessionsStore.ts` (nueva acción
  `createSession`, `initialSessions` vaciado), `frontend/src/stores/chatStore.ts`
  (soporte de hilo vacío para sesiones nuevas, `initialMessages` vaciado),
  `frontend/src/components/Sessions/SessionList.tsx` (nuevo botón/control),
  estilos asociados en el panel colapsado.
- No afecta a `backend/` ni a ningún endpoint existente.
- Cualquier test o fixture del frontend que asuma la presencia de las
  sesiones/mensajes de ejemplo (`s1`-`s5`) deja de ser válido y debe
  actualizarse en este mismo change.
