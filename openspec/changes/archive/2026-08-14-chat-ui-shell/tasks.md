## 1. Dependencias y fuentes

- [x] 1.1 Añadir `zustand` a `frontend/package.json`
- [x] 1.2 Copiar las fuentes ya usadas en la maqueta (`Fraunces`,
      `Public Sans`, `IBM Plex Mono` 400/500, `JetBrains Mono`,
      `Work Sans`) a `frontend/src/assets/fonts/` como `.woff2`

## 2. Sistema de tokens (theme/)

- [x] 2.1 `frontend/src/theme/base.css`: reset, `@font-face` con las
      fuentes locales, tokens de la cáscara de la app (no específicos de
      skin)
- [x] 2.2 `frontend/src/theme/ledger.css`: tokens claro/oscuro de Ledger
      (verde/cian) bajo `[data-skin="ledger"]`, combinados con
      `prefers-color-scheme` y `[data-theme]` tal como en la maqueta
- [x] 2.3 `frontend/src/theme/terminal.css`: tokens claro/oscuro de
      Terminal (ámbar/cian) bajo `[data-skin="terminal"]`
- [x] 2.4 Componentes visuales compartidos por skin (historial, chat,
      fuentes citadas, zona de subida, menú de cuenta) definidos como
      clases CSS que solo usan las custom properties de 2.1–2.3, sin
      duplicar reglas de layout entre skins salvo que la forma del
      componente difiera de verdad (p. ej. filas de ledger vs. filas de
      proceso de terminal)

## 3. Estado (stores/)

- [x] 3.1 `stores/themeStore.ts` (Zustand): `skin` ('ledger'|'terminal'),
      `mode` ('light'|'dark'|null), acciones `setSkin`/`setMode`; efecto
      que sincroniza `data-skin`/`data-theme` en el elemento raíz
- [x] 3.2 `stores/sessionsStore.ts`: sesiones de ejemplo (mismo contenido
      que la maqueta: "Cláusulas de rescisión — Proveedora Ibérica",
      etc.), `activeId`, `renameSession(id, title)`,
      `deleteSession(id)`, `setActive(id)`
- [x] 3.3 `stores/chatStore.ts`: mensajes por sesión (seed con el
      intercambio de ejemplo del contrato), `sendMessage(sessionId, text)`
      que añade el mensaje de usuario y el marcador de posición de
      sistema

## 4. Servicios (services/)

- [x] 4.1 `services/api.ts`: `health()` (llamada real existente, migrada
      desde `App.tsx`), `listModels()` (lista estática envuelta en
      `Promise`, ver design.md decisión 4)
- [x] 4.2 `data/mockModels.ts`: array con los modelos documentados en el
      proposal

## 5. Componentes — Layout

- [x] 5.1 `components/Layout/Header.tsx`: marca, indicador de salud
      (`health()`), selector de identidad (desplegable), toggle de tema
- [x] 5.2 `components/Layout/Sidebar.tsx`: compone SessionList, TagFilter,
      UploadZone, AccountMenu

## 6. Componentes — Sessions / Tags / Documents

- [x] 6.1 `components/Sessions/SessionList.tsx` +
      `components/Sessions/SessionItem.tsx`: título editable
      (`contentEditable` o input controlado), botón eliminar, usa
      `sessionsStore`
- [x] 6.2 `components/Tags/TagFilter.tsx`: chips de tags de ejemplo con
      conteo (legal, técnico, financiero, rrhh, marketing), sin lógica de
      filtrado real todavía (visual únicamente)
- [x] 6.3 `components/Documents/UploadZone.tsx`: zona de drop visual,
      formatos soportados listados, sin handler de subida real

## 7. Componentes — Chat y cuenta

- [x] 7.1 `components/Chat/ChatWindow.tsx` +
      `components/Chat/MessageBubble.tsx`: renderiza mensajes de
      `chatStore` para la sesión activa
- [x] 7.2 `components/Chat/SourcesCited.tsx`: renderiza las fuentes del
      mensaje de ejemplo (documento, página, score) según el componente
      visual de cada skin (recibo con gauge en Ledger, líneas `[src]` en
      Terminal)
- [x] 7.3 `components/Chat/InputBar.tsx`: input controlado, en submit
      llama a `chatStore.sendMessage`
- [x] 7.4 `components/Layout/AccountMenu.tsx`: nombre de usuario como
      control de apertura, selector de tema (sincronizado con
      `themeStore`), selector de modelo (`listModels()`), botón cerrar
      sesión con confirmación visual temporal (sin lógica de auth)

## 8. Integración

- [x] 8.1 Reescribir `frontend/src/App.tsx` para montar `Header` +
      `Sidebar` + `ChatWindow` dentro del layout de dos columnas, aplicando
      `data-skin`/`data-theme` desde `themeStore`
- [x] 8.2 Eliminar el contenido antiguo de health-check en texto plano
      (migrado a `Header`)

## 9. Verificación final

- [x] 9.1 `docker compose up ragvault-frontend` (o `npm run dev`):
      verificar visualmente ambos skins, ambos temas, editar/eliminar una
      sesión, abrir menú de cuenta, enviar un mensaje de chat
- [x] 9.2 `openspec validate chat-ui-shell` sin errores
- [x] 9.3 Ejecutar la skill `ragvault-pattern-review` sobre el diff
