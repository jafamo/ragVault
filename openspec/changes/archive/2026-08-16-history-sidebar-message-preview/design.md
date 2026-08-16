## Context

El panel HISTORIAL (`frontend/src/components/Sessions/SessionList.tsx`,
`SessionItem.tsx`) hoy solo tiene un estado de colapso a nivel de panel
completo (`historyCollapsed` en `frontend/src/stores/sidebarStore.ts`,
persistido en `localStorage`): expandido muestra filas con título editable
y borrado, colapsado muestra una tira de iconos de un carácter por sesión.
Seleccionar una sesión (clic en la fila, en ambos estados) llama a
`setActive(id)` en `sessionsStore`, que sustituye la conversación del
panel central. No existe hoy ningún patrón de expandir/colapsar por fila
(acordeón) en el frontend.

`chatStore.loadMessages(sessionId)` ya es independiente de la sesión
activa: acepta cualquier `sessionId`, cachea el resultado por sesión en
`messagesBySession` y no toca `activeId`. Esto significa que la vista
previa no necesita backend nuevo ni cambios en el store de mensajes, solo
una nueva forma de invocarlo desde la UI sin pasar por `ChatWindow`.

Además, hoy `.app-sidebar` (`Sidebar.tsx:26-31`, con `overflow-y: auto`
definido por skin en `terminal.css:41` y `ledger.css:49`) envuelve
`SessionList`, `TagFilter`, `UploadZone` y `AccountMenu` como hijos
directos, sin contenedor de scroll propio para `SessionList`. Con muchas
sesiones, esto hace que todo el panel lateral se desplace como un único
bloque — `TagFilter`/`UploadZone`/`AccountMenu` pueden quedar fuera de la
vista hasta hacer scroll por todas las sesiones. Este cambio también
corrige eso.

## Goals / Non-Goals

**Goals:**
- Cada fila de sesión, en el estado expandido del panel HISTORIAL, se
  puede expandir individualmente para previsualizar sus mensajes sin
  cambiar la sesión activa del panel central.
- La vista previa reutiliza el mismo mecanismo de carga de mensajes ya
  usado por el chat (`chatStore.loadMessages`), sin nuevas llamadas a la
  API.
- Un control explícito y separado dentro de la vista previa permite
  activar esa sesión en el panel central cuando el usuario lo decide.

- El listado de sesiones tiene su propio scroll vertical, independiente
  del resto del panel: `TagFilter`, `UploadZone` y `AccountMenu` quedan
  siempre visibles sin necesidad de desplazarse por las sesiones para
  llegar a ellos.

**Non-Goals:**
- No se añade vista previa en el estado colapsado del panel (tira de
  iconos): ahí no hay espacio para renderizar mensajes legibles, y el
  clic en un icono sigue activando la sesión directamente, como hoy.
- No se pagina ni se trunca la lista de mensajes a un máximo real de 5 —
  se cargan todos los mensajes de la sesión (ya es lo que hace
  `GET /sessions/{id}/messages`) y se limita la **altura visible** del
  contenedor, no la cantidad de datos.
- No se persiste qué sesión está expandida entre recargas de página (es
  estado de navegación efímero, no una preferencia de usuario como
  `historyCollapsed`).
- El aislamiento de scroll del listado de sesiones no se convierte en una
  preferencia configurable en Ajustes/`AccountMenu`: es comportamiento de
  layout automático (CSS), igual que hoy el colapso a tira de iconos no
  es una opción de Ajustes sino un control propio del panel.

## Decisions

### Estado de fila expandida: local a `SessionList`, no en `sidebarStore`
Se añade un único `expandedId: string | null` como estado de componente en
`SessionList.tsx` (no en el store persistido `sidebarStore`), pasado a
cada `SessionItem` junto con un callback `onTogglePreview(id)`. Al
expandir una sesión se colapsa cualquier otra previamente expandida
(acordeón exclusivo — un solo `expandedId` en vez de un `Set`), para que
la barra no crezca sin límite en su ancho reducido.

Alternativa descartada: guardar `expandedId` en `sidebarStore` con
`persist`. Se descarta porque es estado de navegación, no una preferencia
de usuario como el tema o el colapso del panel — persistirlo generaría
sorpresas (sesión con vista previa abierta al recargar la página sin que
el usuario lo pidiera).

### Altura fija con scroll, no slice de array
La vista previa expandida renderiza *todos* los mensajes ya cargados por
`loadMessages`, dentro de un contenedor con `max-height` equivalente a
~5 filas de mensaje y `overflow-y: auto`. Así los primeros 5 se ven sin
interacción y el resto se alcanza con scroll, sin necesidad de lógica de
paginación ni de truncar los datos reales en el store.

### Componente de fila de mensaje compacto, no reutilizar `MessageBubble`
La vista previa usa un nuevo subcomponente ligero (rol + texto truncado a
una o dos líneas con `text-overflow: ellipsis`) en vez de `MessageBubble`,
que está pensado para el ancho completo del panel central y no cabe con
legibilidad en el ancho reducido de la barra de historial.

### Activar sesión: control separado del toggle de expandir
Dentro de la vista previa expandida aparece un botón explícito ("Abrir en
el chat") que llama a `setActive(id)`. El clic en el título/fila de la
sesión (fuera del área de mensajes) sigue alternando solo
expandir/colapsar la vista previa — no cambia la sesión activa por sí
solo, para que el usuario pueda ojear varias sesiones sin perder de vista
la conversación en la que está.

### Scroll aislado al listado de sesiones, no a `.app-sidebar`
`.app-sidebar` deja de declarar `overflow-y: auto` en `terminal.css` y
`ledger.css`; en su lugar, `Sidebar.tsx` pasa a ser un contenedor flex en
columna donde solo el wrapper que envuelve `SessionList` recibe `flex: 1;
min-height: 0; overflow-y: auto` — el patrón estándar para que un hijo
flex haga scroll interno sin que el contenedor padre se estire. `TagFilter`,
`UploadZone` y `AccountMenu` quedan fuera de ese wrapper, con altura fija,
por lo que nunca requieren scroll para ser alcanzados. Esto aplica igual
en el estado colapsado del panel (tira de iconos): el wrapper con scroll
envuelve la tira de sesiones, no el resto de controles simplificados.

Alternativa descartada: mantener `overflow-y: auto` en `.app-sidebar` y
limitar visualmente cuántas sesiones se muestran (paginación). Se
descarta porque complica el listado sin resolver el problema real — el
usuario sigue queriendo ver todas sus sesiones, solo que sin que eso
desplace el resto del panel fuera de vista.

### Carga perezosa y caché reutilizada
Expandir una sesión por primera vez dispara `loadMessages(id)`; gracias a
la caché existente por `loadedSessions[id]`, volver a expandir la misma
sesión no repite la petición. Mientras se resuelve la primera carga se
muestra un indicador de carga compacto dentro de la fila.

## Risks / Trade-offs

- **[Riesgo]** El ancho reducido del panel de historial limita la
  legibilidad de los mensajes en preview → **Mitigación**: truncado con
  ellipsis y tipografía compacta, coherente con el resto de `SessionItem`.
- **[Riesgo]** Expandir muchas sesiones distintas seguidas dispara varias
  peticiones de mensajes → **Mitigación**: ya mitigado por la caché
  existente de `chatStore`; no hace falta trabajo adicional.
- **[Trade-off]** No hay indicador visual de "tiene más de 5 mensajes,
  desplázate" más allá del propio scrollbar del contenedor — aceptable
  para una primera versión; se puede añadir un degradado o flecha en un
  change posterior si resulta poco descubrible.

## Migration Plan

Sin migración de datos ni cambios de backend. Cambio de frontend puro,
desplegable de forma independiente.

## Open Questions

Ninguna pendiente.
