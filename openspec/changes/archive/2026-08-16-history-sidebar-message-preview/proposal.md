## Why

Hoy, para ver de qué trataba una sesión anterior, el usuario tiene que
hacer clic en ella y sustituir la conversación activa del panel central,
perdiendo de vista en qué estaba trabajando. El panel HISTORIAL solo
ofrece colapsar/expandir todo el panel (tira de iconos vs. listado
completo), no una vista previa por sesión. Añadir una vista previa de
mensajes directamente en la barra vertical de historial permite
inspeccionar una sesión sin abandonar la conversación activa.

## What Changes

- Cada fila de sesión en el panel HISTORIAL (`SessionItem`) gana un
  control de expandir/colapsar (acordeón por fila, nuevo patrón en la UI
  — hoy solo existe el colapso a nivel de panel completo en
  `sidebarStore`).
- Al expandir una sesión, se muestran sus mensajes en orden cronológico
  dentro de la propia barra, en un contenedor con scroll cuya altura
  visible corresponde aproximadamente a los 5 primeros mensajes — el
  resto de mensajes de esa sesión se alcanza haciendo scroll dentro de
  esa vista previa, sin cambiar la sesión activa del panel central.
- La vista previa reutiliza `chatStore.loadMessages(sessionId)`, que ya
  admite cargar mensajes de cualquier sesión de forma independiente de
  cuál esté activa (`activeId`), sin necesidad de tocar el store de
  sesiones ni el endpoint `GET /sessions/{id}/messages`.
- Cada sesión expandida gana un control explícito ("Abrir en el chat" o
  equivalente) que, al pulsarlo, activa esa sesión en el panel central
  (`setActive(id)`) — comportamiento distinto y separado de expandir la
  vista previa, que solo con el clic en la fila no cambia hoy la
  conversación activa.
- Solo una sesión puede tener su vista previa expandida a la vez dentro
  de la barra (acordeón exclusivo), para mantener la barra manejable en
  el ancho reducido del panel de historial.
- El listado de sesiones del panel HISTORIAL gana su propio scroll
  vertical, aislado del resto del panel: hoy `.app-sidebar` hace scroll
  como un único bloque (`SessionList`, `TagFilter`, `UploadZone` y
  `AccountMenu` juntos), así que con muchas sesiones hay que desplazarse
  por todo el historial para llegar a los tags, la zona de subida o el
  menú de cuenta. Tras este cambio, solo el listado de sesiones
  desplaza internamente; `TagFilter`, `UploadZone` y `AccountMenu`
  quedan siempre visibles, sin necesidad de scroll para alcanzarlos. Es
  comportamiento automático de layout (CSS), no una preferencia
  configurable en Ajustes/`AccountMenu`.

## Capabilities

### New Capabilities

(ninguna)

### Modified Capabilities

- `chat-ui-shell`: el requirement "Historial de sesiones editable" se
  amplía con el comportamiento de vista previa de mensajes por sesión
  (expandir/colapsar fila, scroll interno, y control separado para
  activar la sesión en el panel central).

## Impact

- Frontend: `frontend/src/components/Sessions/SessionItem.tsx` (nuevo
  estado de expandido/colapsado por fila y renderizado de la lista de
  mensajes), `frontend/src/components/Sessions/SessionList.tsx` (asegurar
  que solo una fila esté expandida a la vez, y envolver el listado de
  sesiones en su propio contenedor con scroll), `frontend/src/stores/`
  (posible estado local de "fila expandida" — a decidir en el diseño si
  vive en `sidebarStore` o como estado de componente),
  `frontend/src/components/Layout/Sidebar.tsx` y
  `frontend/src/theme/{base,terminal,ledger}.css` (mover `overflow-y:
  auto` de `.app-sidebar` a un contenedor propio del listado de
  sesiones).
- Sin cambios de backend: reutiliza `GET /sessions/{id}/messages` y
  `chatStore.loadMessages` ya existentes, sin nuevas rutas ni cambios de
  esquema.
