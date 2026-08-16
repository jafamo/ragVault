## Context

`sessionsStore` (`frontend/src/stores/sessionsStore.ts`) mantiene una
lista fija de sesiones de ejemplo en memoria y un `activeId`. `chatStore`
(`frontend/src/stores/chatStore.ts`) guarda los mensajes en
`messagesBySession: Record<string, Message[]>`, indexados por el id de
sesión, y `sendMessage(sessionId, text)` ya opera por sesión. No existe
ningún endpoint de backend de sesiones (`chat-sessions` es una capability
futura del plan) — todo esto sigue siendo un mock de frontend, igual que
el resto de `chat-ui-shell`.

## Goals / Non-Goals

**Goals:**
- Permitir crear una sesión nueva y vacía desde la UI con un solo clic.
- Que la sesión nueva no arrastre mensajes de otras sesiones.
- Que el control esté disponible tanto con el historial expandido como
  colapsado (`SessionList` ya renderiza ambos modos, ver spec de
  `chat-ui-shell` — "Colapsar el historial").
- Evitar acumular sesiones vacías duplicadas si el usuario pulsa el botón
  repetidamente sin escribir nada.
- Retirar del frontend las sesiones y mensajes de ejemplo (`s1`-`s5`) para
  que el historial mostrado sea siempre estado real de la sesión de
  usuario (aunque sea solo en memoria), no datos de demo.

**Non-Goals:**
- Persistencia real de sesiones en backend/BD (queda para la capability
  `chat-sessions`).
- Borrado/renombrado de la sesión nueva (ya cubierto por requisitos
  existentes de "Historial de sesiones editable").
- Cambios en el contrato de `POST /chat` o en `sources`/`retriever_config`.
- Migrar o conservar en ningún sitio el contenido de las conversaciones de
  ejemplo eliminadas: son datos de demo desechables, no datos de usuario.

## Decisions

- **Dónde vive la lógica de creación**: `createSession` se añade como
  acción de `sessionsStore`, no de `chatStore`, porque la sesión (id,
  título, tag, tiempo) es responsabilidad de `sessionsStore`; `chatStore`
  simplemente no tendrá entrada en `messagesBySession` para el id nuevo, lo
  cual ya es un estado válido (la UI debe tratar "sin entrada" como hilo
  vacío, no como error).
- **Id de sesión nuevo**: generado con un contador/prefijo local
  (`local-session-N`), siguiendo el mismo patrón que `nextId()` en
  `chatStore` para los mensajes locales — no se introduce ninguna
  dependencia UUID nueva.
- **Reutilizar sesión vacía activa**: antes de crear, `createSession`
  comprueba si `activeId` ya apunta a una sesión sin mensajes
  (`messagesBySession[activeId]` vacío o inexistente); si es así, no crea
  nada y deja la sesión activa como está. Esto evita una acumulación
  trivial de sesiones vacías al hacer clic varias veces, sin necesitar un
  límite arbitrario ni lógica de deduplicación más compleja.
- **Posición en la lista y título por defecto**: la sesión nueva se
  inserta al principio (más reciente primero, consistente con el orden
  actual por `time`) con título "Nueva conversación" y `tag: ""`, editable
  después con el requisito ya existente de renombrado.
- **Control colapsado**: se reutiliza el mismo patrón de icono-only que ya
  usan `TagFilter`/`UploadZone`/`AccountMenu` en el modo colapsado del
  panel, sin introducir un componente de icono nuevo si ya hay uno
  disponible en el set de iconos del proyecto.
- **Estado inicial sin mocks**: `initialSessions` e `initialMessages` se
  vacían por completo en vez de reducirse a una sesión de ejemplo
  "realista", para no dejar ningún dato inventado en el historial. El
  estado de arranque de `sessionsStore` no se deja con `sessions: []` y
  `activeId: ""` (eso obligaría a la UI a manejar "sin sesión activa" como
  caso especial en `SessionList`, `chatStore.sendMessage`, etc.); en su
  lugar, el store se inicializa creando una sesión vacía con la misma
  función que usa el botón "Nuevo chat" (ver 1.3 de `tasks.md`), de modo
  que "arrancar la app" y "pulsar Nuevo chat" comparten un único camino de
  código en vez de dos implementaciones de "sesión vacía" a mantener en
  paralelo.

## Error Handling

- **Id duplicado**: el contador local (`local-session-N`) es compartido y
  monotónico dentro de la sesión de navegador (mismo mecanismo que
  `nextId()` en `chatStore`), por lo que no puede colisionar consigo
  mismo; no se necesita comprobación de unicidad adicional.
- **`activeId` sin sesión correspondiente**: si `createSession` (o el
  bootstrap inicial) deja `activeId` apuntando a un id que no existe en
  `sessions` — por ejemplo por un bug en la comprobación de "sesión activa
  vacía" — `SessionList` y `chatStore` SHALL tratarlo como "ninguna sesión
  activa": no debe lanzar (no indexar `sessions.find(...)` sin comprobar
  `undefined`), sino caer al primer elemento de `sessions` si existe, o al
  estado vacío si `sessions` está vacío.
- **Lectura de `messagesBySession[activeId]` inexistente**: ya es un
  estado válido (hilo vacío) según los Non-Goals; `createSession` SHALL
  leerlo con `?? []` al comprobar si la sesión activa está vacía, igual
  que el resto del código que consume `messagesBySession`.
- **`deleteSession` deja el historial sin sesiones**: `sessionsStore.deleteSession`
  ya fija `activeId: sessions[0]?.id ?? ""` al borrar la última sesión: con
  el historial arrancando vacío por defecto (ver "Estado inicial sin
  mocks"), este es ahora un camino alcanzable en uso normal, no solo un
  caso extremo teórico. `deleteSession` SHALL invocar la misma lógica de
  `createSession` cuando el borrado deja `sessions` vacío, para no dejar
  nunca la app sin ninguna sesión activa ni forzar a la UI a manejar
  "cero sesiones" como estado aparte.
- No se añade manejo de errores para fallos de red, storage o backend en
  este change: `createSession`/`deleteSession` son operaciones síncronas
  sobre estado en memoria de Zustand y no tienen ninguna vía de fallo de
  I/O que capturar.

## Risks / Trade-offs

- [Doble clic rápido crea dos sesiones antes de que el estado se
  re-renderice] → La comprobación de "sesión activa vacía" se hace dentro
  del mismo `set()` de Zustand (lectura-y-escritura atómica), no en un
  efecto separado, por lo que no hay ventana de carrera entre clics.
- [El id local (`local-session-N`) colisiona en el futuro con ids reales
  del backend cuando se implemente `chat-sessions`] → Aceptable por ahora;
  ese futuro change deberá migrar el esquema de ids de todas formas
  (sesiones y mensajes ya usan el prefijo `local-` con la misma
  limitación conocida).
