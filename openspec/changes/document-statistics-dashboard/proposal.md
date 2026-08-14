## Why

El usuario no tiene forma de saber, de un vistazo, cuántos documentos hay
cargados por tipo, cuántos siguen pendientes de procesar, cuáles han
fallado y por qué, con qué ritmo se está ingiriendo el vault, ni cómo se
distribuyen por temática. Esta información ya existe en `documents`
(`format`, `status`, `error_message`, `uploaded_at`) pero no se expone en
ningún sitio de la UI. Sin ella, un error de ingesta silencioso (p. ej. un
loader fallando repetidamente para un formato) puede pasar desapercibido.

## What Changes

- Nuevo botón en el panel de ajustes (`AccountMenu.tsx`) que alterna la
  vista principal entre el chat y un dashboard de estadísticas (toggle
  in-place sobre el mismo layout, sin añadir router).
- Nuevo dashboard de estadísticas con gráficos (Recharts, nueva
  dependencia de frontend) mostrando:
  - Recuento de documentos por tipo/formato.
  - Documentos pendientes de procesar (`status="queued"`/`"processing"`).
  - Documentos con error, listados junto a su `error_message`.
  - Documentos ingeridos por franja temporal relativa a hoy (últimos 5,
    15, 30, 90 y 365 días, según `uploaded_at`).
  - Distribución de documentos por tag/temática.
- Modelo mínimo de tags en el backend (`Tag`, asociación
  `document_tags`) y endpoint para asignar/listar tags de un documento,
  necesario para poder agregar la última métrica. **No** incluye el
  auto-tagger por LLM de una fase posterior del plan — los tags se
  asignan manualmente por ahora.
- Nuevos endpoints de agregación (`GET /stats/*`) que exponen los datos
  anteriores ya agregados, vía un `StatsRepository` (sin acceso directo a
  SQL desde las rutas).

## Capabilities

### New Capabilities
- `document-statistics`: dashboard de estadísticas (endpoints de
  agregación + vista de frontend con gráficos) sobre documentos por
  formato, estado, franja temporal y tag.
- `document-tags`: modelo mínimo de tags y su asociación con documentos
  (creación, asignación manual, listado), base para la agregación por
  tag y para futuros changes de auto-tagging.

### Modified Capabilities
- `chat-ui-shell`: el panel de ajustes (`AccountMenu`) gana un control
  para alternar la vista principal entre chat y estadísticas.

## Impact

- Backend: nuevo modelo `Tag`/`document_tags` en
  `backend/app/models/entities.py`, nuevo `StatsRepository` y
  `TagRepository` en `backend/app/repositories`, nuevas rutas en
  `backend/app/api/routes` (`/stats/*`, `/documents/{id}/tags`), logging
  estructurado de estas rutas vía `core/logging.py`.
- Frontend: nueva dependencia `recharts`; nuevos componentes bajo
  `frontend/src/components/Stats/`; extensión de un store de Zustand (o
  uno nuevo) para la vista activa (chat/estadísticas); botón nuevo en
  `AccountMenu.tsx`; nuevas llamadas en `frontend/src/services/api.ts`.
- Sin impacto en el pipeline RAG, en la ingesta de documentos, ni en
  Ollama/ChromaDB.
