## Why

El frontend actual (`project-bootstrap`) es solo una página que confirma
que el backend responde. El usuario ha validado dirección visual sobre una
maqueta (artifact) con dos identidades — "Ledger" (bóveda, verde/cian) y
"Terminal" (runtime local, ámbar) — y quiere ambas disponibles,
intercambiables, en vez de elegir una sola. El backend todavía no expone
endpoints de chat/sesiones/documentos (eso es `rag-pipeline-basico`), así
que construir la UI real ahora, sobre datos de ejemplo, desacopla el
trabajo de diseño del trabajo de pipeline RAG y deja ambos avanzar en
paralelo.

## What Changes

- Sustituir `frontend/src/App.tsx` (la página mínima de `/health`) por una
  aplicación de chat real: sidebar (historial + filtro de tags + zona de
  subida + menú de cuenta) y panel principal (transcripción de chat con
  fuentes citadas).
- Dos identidades visuales completas y coexistentes — `ledger` y
  `terminal` — seleccionables en caliente desde un desplegable, cada una
  con su propio conjunto de tokens de color/tipografía y variantes claro/
  oscuro (siguiendo la paleta validada en la maqueta: Ledger en verde/cian,
  Terminal en ámbar/cian).
- Toggle de tema claro/oscuro independiente del diseño elegido, persistido
  solo en memoria de la sesión del navegador (sin backend todavía).
- Historial de sesiones **editable**: renombrar título in situ, eliminar
  sesión — sobre datos de ejemplo en memoria (Zustand), sin persistencia
  real.
- Menú de cuenta (sustituye a un simple "Ajustes"): muestra el nombre del
  usuario logueado, selector de tema, selector de modelo (lista estática
  por ahora, ver Impact) y botón de cerrar sesión (stub visual, sin lógica
  de auth real — no hay sistema de autenticación en este proyecto).
- Zona de subida de documentos: solo UI (drag target, lista de formatos
  soportados) — no dispara ninguna llamada real de ingesta todavía.
- Chat: input funcional que añade el mensaje del usuario al hilo de
  ejemplo y responde con un mensaje de marcador de posición explícito
  (no genera respuestas reales — no hay pipeline RAG conectado).
- El health check real contra el backend (`GET /health`, ya implementado)
  se conserva e integra en la cabecera de la app en vez de en un párrafo
  suelto.

Fuera de alcance (quedan para `rag-pipeline-basico` u otros changes):
conexión real a `/chat`, `/upload`, `/sessions`, `/tags`; persistencia de
sesiones; autenticación real; listado de modelos vía API (por ahora
estático, ver Impact).

## Capabilities

### New Capabilities

- `chat-ui-shell`: shell de interfaz de chat con dos identidades visuales
  intercambiables (Ledger, Terminal), tema claro/oscuro, historial editable
  sobre datos de ejemplo, menú de cuenta y health check real integrado.

### Modified Capabilities

(ninguna — la spec existente `project-scaffolding` solo exige que el
frontend muestre el resultado de `GET /health` en algún sitio, lo cual
sigue cumpliéndose dentro de la nueva cabecera de la app)

## Impact

- Código nuevo: `frontend/src/theme/**`, `frontend/src/stores/**`,
  `frontend/src/data/**` (datos de ejemplo), `frontend/src/components/**`
  (Layout, Sessions, Tags, Documents, Chat), fuentes auto-alojadas en
  `frontend/src/assets/fonts/`.
- Código modificado: `frontend/src/App.tsx`, `frontend/package.json`
  (nuevas dependencias: `zustand`).
- Sin cambios en el backend ni en su API pública.
- El listado de modelos del menú de cuenta es estático en este change
  (copiado de los modelos reales disponibles en el Ollama del usuario en el
  momento de diseñar la maqueta) — pasar a consultarlo vía API es trabajo
  futuro (necesitaría un endpoint tipo `GET /models` que no existe aún).
- Decisión de estilo: no se introduce Tailwind CSS pese a que
  `rag_vault_plan.md` §3.2 lo sugiere — se documenta el motivo en
  `design.md`.
