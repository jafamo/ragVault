## 1. Store: sessionsStore

- [x] 1.1 Eliminar los datos mock del historial: vaciar `initialSessions` en `frontend/src/stores/sessionsStore.ts` (y `initialMessages` en `frontend/src/stores/chatStore.ts`) para que el historial arranque sin sesiones de ejemplo (`s1`-`s5`) en el frontend; `activeId` inicial pasa a ser el de una sesión nueva creada al arrancar (ver 1.3), no un id fijo hardcodeado.
- [x] 1.2 Añadir `createSession` a `sessionsStore` (`frontend/src/stores/sessionsStore.ts`): genera un id local único (`local-session-N`, mismo patrón que `nextId()` de `chatStore`), inserta la sesión nueva (título "Nueva conversación", `tag: ""`, `time: "ahora"`) al principio de `sessions`, y la marca como `activeId`.
- [x] 1.3 Si `initialSessions` queda vacío, inicializar el store con una única sesión creada vía la misma lógica que `createSession` (evita duplicar la fórmula de "sesión nueva" entre el arranque y el botón).
- [x] 1.4 Antes de crear una sesión nueva desde el botón, comprobar dentro del mismo `set()` si la sesión activa ya está vacía (leyendo `useChatStore.getState().messagesBySession[activeId] ?? []`); si lo está, no crear ninguna sesión nueva y dejar el estado igual.
- [x] 1.5 Actualizar `deleteSession` para que, cuando borrar deja `sessions` vacío, cree automáticamente una sesión nueva (misma lógica que `createSession`) en vez de fijar `activeId: ""`; la app nunca debe quedarse sin ninguna sesión activa.

## 2. Store: chatStore

- [x] 2.1 Verificar/asegurar que `messagesBySession` trata una entrada inexistente como hilo vacío en toda la UI que la consuma (no solo donde ya se usa `?? []`), de forma que una sesión recién creada no requiera inicialización explícita.
- [x] 2.2 Añadir una guarda en los puntos que indexan `sessions` por `activeId` (`SessionList`, `chatStore`, etc.) para que un `activeId` sin sesión correspondiente no lance: caer al primer elemento de `sessions` si existe, o a estado vacío si no.

## 3. UI: SessionList

- [x] 3.1 Añadir un botón "Nuevo chat" en `frontend/src/components/Sessions/SessionList.tsx` (modo expandido) que llame a `createSession` y luego `setActive` con el id devuelto.
- [x] 3.2 Añadir el control equivalente en icono-only para el modo colapsado del panel (mismo patrón visual que los demás controles colapsados de `Sidebar`).
- [x] 3.3 Aplicar estilos consistentes con el resto de controles del historial (identidades Ledger y Terminal, tema claro/oscuro).

## 4. Verificación

- [x] 4.1 Probar manualmente: crear sesión nueva desde expandido, desde colapsado, pulsar dos veces seguidas sin escribir (no debe duplicar), y confirmar que el hilo de mensajes no mezcla contenido entre sesiones.
- [x] 4.2 Ejecutar `ragvault-pattern-review` sobre el diff antes de `git flow feature finish`.
