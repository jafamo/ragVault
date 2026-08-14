## 1. Estado

- [x] 1.1 `frontend/src/stores/sidebarStore.ts`: store Zustand con
      `historyCollapsed: boolean` y `toggleHistoryCollapsed()`, persistido
      en `localStorage` vía `zustand/middleware` `persist`

## 2. Componentes de historial

- [x] 2.1 `SessionList.tsx`: añadir botón de colapsar/expandir junto al
      label "Historial"/`sessions --sort=recent`; cuando
      `historyCollapsed` es `true`, renderiza `SessionItem` en modo
      compacto en vez del listado completo
- [x] 2.2 `SessionItem.tsx`: variante compacta (prop `collapsed`) que
      muestra solo un icono/inicial de la sesión (sin título, tag ni
      controles de editar/eliminar) mientras colapsado; conserva
      `onClick` para activar la sesión
- [x] 2.3 Estilos: ancho fijo estrecho para el estado colapsado en ambas
      identidades visuales (Ledger y Terminal), transición suave al
      colapsar/expandir

## 2b. Responsive: auto-colapso en móvil

- [x] 2b.1 `sidebarStore.ts`: añadir `setHistoryCollapsed(collapsed)`
      además de `toggleHistoryCollapsed()`
- [x] 2b.2 `Sidebar.tsx`: al montar y al cruzar el breakpoint
      `(max-width: 768px)` vía `matchMedia`, forzar
      `historyCollapsed = true`; no revierte automáticamente si el
      usuario lo expande manualmente estando en móvil

## 3. Cabecera y Ajustes

- [x] 3.1 `Header.tsx`: quitar el `<select>` de "Diseño" y los botones
      "Claro"/"Oscuro"; añadir un botón único con icono sol/luna que
      alterna `mode` vía `setMode`
- [x] 3.2 `AccountMenu.tsx`: añadir fila "Diseño" con el mismo control
      (`select` o segmented) que hoy vive en `Header.tsx`, usando
      `setSkin` de `themeStore`

## 4. Revisión final

- [x] 4.1 Ejecutar la skill `ragvault-pattern-review` sobre el diff antes
      de `git flow feature finish`
- [x] 4.2 `npm run build` (type-check) sin errores
- [x] 4.3 Probar manualmente con `npm run dev` en ambas identidades
      visuales y en viewport estrecho (responsive): el chat gana espacio
      al colapsar el historial, y Ajustes/cabecera quedan coherentes
      (icono único de tema, selector de diseño en Ajustes). Verificado
      con capturas reales (Playwright) en Ledger/Terminal ×
      expandido/colapsado; detectó y corrigió texto roto de `TagFilter`
      y del panel de Ajustes cuando queda abierto en modo estrecho
