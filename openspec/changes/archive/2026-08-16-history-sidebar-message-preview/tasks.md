## 1. Estado de acordeón en el panel

- [x] 1.1 Añadir estado `expandedId: string | null` en
      `frontend/src/components/Sessions/SessionList.tsx` (componente
      local, sin persistir), con un handler `handleTogglePreview(id)` que
      colapsa cualquier otra fila expandida al abrir una nueva.
- [x] 1.2 Pasar `expandedId` y `onTogglePreview` como props a cada
      `SessionItem` desde `SessionList.tsx`.
- [x] 1.3 Al colapsar el panel completo (`historyCollapsed` pasa a
      `true`), resetear `expandedId` a `null` para que no quede estado de
      vista previa colgando al volver a expandir el panel.

## 2. Fila de sesión con vista previa

- [x] 2.1 En `frontend/src/components/Sessions/SessionItem.tsx`, añadir
      un control de expandir/colapsar vista previa visible solo en la
      variante expandida del panel (no en la rama de renderizado
      colapsado de líneas 33-45), distinto del área de título/clic que
      hoy llama a `setActive`.
- [x] 2.2 Al expandir una fila, invocar `chatStore.loadMessages(id)`
      (ya idempotente/cacheado por `loadedSessions`) y mostrar un
      indicador de carga compacto mientras se resuelve la primera carga.
- [x] 2.3 Crear un subcomponente de fila de mensaje compacto (rol + texto
      truncado a 1-2 líneas con ellipsis) para la vista previa — no
      reutilizar `MessageBubble`, pensado para el ancho completo del chat.
- [x] 2.4 Renderizar los mensajes de `messagesBySession[id]` dentro de un
      contenedor con `max-height` equivalente a ~5 filas y
      `overflow-y: auto`, sin recortar el array de datos.
- [x] 2.5 Añadir dentro de la vista previa expandida un botón explícito
      ("Abrir en el chat") que llama a `setActive(id)` de
      `sessionsStore`, separado del control de expandir/colapsar.

## 3. Scroll aislado del listado de sesiones

- [x] 3.1 En `frontend/src/theme/terminal.css:41` y
      `frontend/src/theme/ledger.css:49`, quitar `overflow-y: auto` de la
      regla `.app-sidebar`.
- [x] 3.2 En `frontend/src/components/Layout/Sidebar.tsx`, envolver
      `<SessionList />` en un contenedor propio (p. ej.
      `.app-sidebar-sessions`) y añadir esa clase en `base.css` con
      `flex: 1; min-height: 0; overflow-y: auto`, dejando `.app-sidebar`
      como flex-column sin scroll propio.
- [x] 3.3 Verificar que `TagFilter`, `UploadZone` y `AccountMenu`
      quedan fuera del contenedor con scroll, con altura fija, tanto en
      el estado expandido del panel como en el colapsado (tira de
      iconos).
- [x] 3.4 Comprobar que no se introduce ningún control nuevo en
      `AccountMenu`/Ajustes para este comportamiento.

## 4. Verificación manual

- [x] 4.1 Probar en la app real (`/run`): expandir una sesión con menos
      de 5 mensajes (sin scroll visible), expandir una con más de 5
      (scroll dentro de la vista previa), expandir una sesión distinta y
      comprobar que la anterior se colapsa sola.
- [x] 4.2 Comprobar que pulsar "Abrir en el chat" cambia la conversación
      del panel central sin alterar la vista previa expandida en el
      historial.
- [x] 4.3 Comprobar que colapsar el panel completo oculta cualquier vista
      previa abierta, y que al reexpandir el panel ninguna fila queda
      expandida por defecto.
- [x] 4.4 Comprobar en viewport móvil (≤768px) que el comportamiento de
      colapso automático existente no interfiere con el nuevo control por
      fila (el control de vista previa simplemente no es alcanzable en la
      tira de iconos, como está definido).
- [x] 4.5 Probar con muchas sesiones (>15) que el listado hace scroll
      internamente y que `TagFilter`/`UploadZone`/`AccountMenu` permanecen
      visibles sin desplazarse, tanto expandido como colapsado.
- [x] 4.6 Ejecutar la skill `ragvault-pattern-review` sobre el diff antes
      de `git flow feature finish`.
- [x] 4.7 Añadir entrada en `CHANGELOG.md` bajo `[Sin publicar]` (`Added`)
      describiendo la vista previa de mensajes por sesión y el scroll
      aislado del listado de historial, referenciando el change
      `history-sidebar-message-preview`.
