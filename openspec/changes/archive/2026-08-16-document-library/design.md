## Context

El `Document` actual (`backend/app/models/entities.py`) guarda `id`,
`filename`, `format`, `uploaded_at`, `chunk_count`, `status`,
`error_message` y la relación M:N con `Tag`. No guarda tamaño ni ruta
absoluta del fichero en disco, y no hay endpoint para listar todos los
documentos ni para eliminarlos. `DocumentRepository` solo tiene `create`,
`get`, `list()` y `update_status`. La vista de menú es un switch en
`viewStore` (`"chat" | "stats"`) leído por `App.tsx` y controlado desde
`AccountMenu.tsx`; no hay `react-router`, todo es render condicional.

## Goals / Non-Goals

**Goals:**
- Listar todos los documentos ingeridos con estado, título, tipo, tamaño,
  tags y ruta absoluta, con filtro por columna, en una tabla ordenable.
- Permitir eliminar un documento: borra su fila SQL, sus relaciones de
  tags, sus chunks/embeddings en ChromaDB y el fichero físico.
- Persistir `size_bytes` y `absolute_path` desde el momento de la subida.

**Non-Goals:**
- Paginación en servidor (con el volumen esperado de MVP, filtrado y
  orden se hacen en cliente sobre el listado completo de `GET /documents`).
- Edición de tags o metadata desde la biblioteca (ya cubierto por
  `document-tags`); solo se muestran y se enlaza al flujo existente.
- Papelera/soft-delete o confirmación de eliminación en dos pasos más allá
  de un diálogo de confirmación simple en la UI.

## Decisions

- **Backfill de documentos existentes**: `absolute_path` y `size_bytes` se
  añaden como columnas nullable en la migración Alembic. Para filas
  existentes, un paso de backfill en la propia migración intenta
  `os.path.getsize` sobre la ruta reconstruida desde el directorio de
  uploads configurado; si el fichero ya no existe, deja `size_bytes=NULL`
  y `absolute_path=NULL` y el documento se muestra en la tabla con esos
  campos como "—". Alternativa descartada: exigir re-subida manual de todo
  el corpus — inaceptable como experiencia de migración.
- **Eliminación en dos fases (vector store y fichero primero, SQL al
  final)**: `DELETE /documents/{id}` borra primero los chunks del vector
  store (`VectorStoreRepository.delete_by_document_id`), luego el fichero
  físico (best-effort, con log si no existe) y por último la fila SQL (con
  `ON DELETE CASCADE` en `document_tags`). Si falla el borrado del vector
  store se aborta antes de tocar SQL, para no dejar metadata "fantasma" sin
  chunks reales pero sí con inconsistencia inversa (chunks huérfanos sin
  fila SQL) — se prefiere el error visible sobre el estado inconsistente
  silencioso.
- **Cancelación de ingesta en curso en vez de bloquear el borrado**: cuando
  `DELETE /documents/{id}` se invoca sobre un documento `status="processing"`,
  el sistema NO rechaza la operación con 409; en su lugar cancela la
  ingesta en curso y continúa con el borrado. Mecanismo: un registro en
  memoria `CancellationRegistry` (mismo estilo que el `IngestionProgressTracker`
  ya existente en `backend/app/core/progress.py`: dict guardado con
  `threading.Lock`, sin persistencia en BD) en
  `backend/app/core/cancellation.py`. `DELETE` llama a
  `cancellation_registry.request_cancel(document_id)`; `run_ingestion`
  (`backend/app/document_processing/ingestion_pipeline.py`) comprueba
  `cancellation_registry.is_cancelled(document_id)` entre etapas (tras el
  loader, tras el chunking, entre cada lote de embeddings, y una última
  vez tras terminar de indexar y antes de marcar `status="done"`) y, si está
  marcado, aborta lanzando `IngestionCancelled`, que el propio
  `run_ingestion` captura para marcar `status="cancelled"` sin tratarlo
  como `error`. El endpoint `DELETE` espera (poll corto, con timeout,
  p.ej. 5s con intervalos de 100ms) a que el documento salga de
  `processing` antes de proceder al borrado de vector store/fichero/fila;
  si se agota el timeout, continúa igualmente con el borrado best-effort
  (el pipeline, al comprobar cancelación en su siguiente punto de control,
  no seguirá escribiendo más chunks). Alternativa descartada: mantener el
  409 y exigir que el usuario espere a que termine la ingesta — mala
  experiencia para documentos grandes o colgados, y es justo el caso de
  uso que motiva tener un botón de eliminar visible en todo momento.
- **Filtrado en cliente vs servidor**: se filtra en el frontend sobre el
  array devuelto por `GET /documents`, igual que `TagFilter` ya hace con
  tags. Evita añadir query params y paginación al backend en esta fase;
  revisar si el volumen de documentos crece mucho (fuera de alcance ahora).
- **Reutilizar el patrón de `ErrorsTable`**: la tabla de biblioteca sigue
  la misma convención de markup/CSS que `ErrorsTable.tsx` en vez de
  introducir una librería de datatables nueva (no hay ninguna en
  `package.json` y el plan no la menciona como dependencia del stack).
- **Tercer valor de vista `"library"`**: se añade al mismo `viewStore` y al
  mismo grupo de botones de `AccountMenu`, no una ruta nueva, manteniendo
  la ausencia de `react-router` consistente con el resto de la app.

## Risks / Trade-offs

- [Backfill deja huecos si los ficheros originales se movieron o
  borraron manualmente fuera de la app] → se documenta como comportamiento
  esperado (campos "—" en la tabla) en vez de bloquear la migración.
- [Borrar el fichero físico es irreversible y no hay papelera] → el botón
  Eliminar de la UI pide confirmación explícita antes de llamar al
  endpoint.
- [Filtrado 100% en cliente no escala indefinidamente] → aceptable para el
  volumen de MVP; revisar en una fase posterior si se detecta degradación.
- [Condición de carrera entre la señal de cancelación y el hilo de
  ingesta, que puede escribir un lote de embeddings justo después de
  comprobar el flag] → aceptable: el borrado del vector store por
  `document_id` ocurre después del poll de cancelación, así que cualquier
  chunk residual escrito en ese margen queda igualmente eliminado.

## Migration Plan

1. Migración Alembic: añade `documents.size_bytes` (`INTEGER NULL`) y
   `documents.absolute_path` (`TEXT NULL`), con backfill best-effort para
   filas existentes.
2. Backend: actualizar `DocumentRepository.create` para recibir y guardar
   ambos campos; añadir `DocumentRepository.list_all()` (alias claro de
   `list()` si se reutiliza) y `DocumentRepository.delete(id)`.
3. Backend: pipeline de ingesta (`POST /upload`) calcula `size_bytes` y
   `absolute_path` al guardar el fichero subido, antes de crear el
   `Document`.
4. Backend: nuevo `backend/app/core/cancellation.py` (`CancellationRegistry`)
   y puntos de comprobación de cancelación en `run_ingestion`; nuevo
   estado `status="cancelled"` manejado como terminal (no `error`).
5. Backend: nuevos endpoints `GET /documents` y `DELETE /documents/{id}`
   en `backend/app/api/routes/documents.py`, este último cancelando la
   ingesta en curso si `status="processing"` antes de borrar.
6. Frontend: `viewStore` con `"library"`, botón en `AccountMenu`, nuevo
   componente `DocumentLibrary` + servicio de API, integrado en `App.tsx`.
7. Sin rollback especial: la migración es aditiva (columnas nullable); un
   rollback de Alembic estándar (`downgrade`) las elimina sin pérdida de
   datos de las columnas preexistentes.

## Open Questions

Ninguna pendiente: se confirmó que borrar un documento `processing` SHALL
cancelar la ingesta en curso en vez de rechazar la operación (ver decisión
"Cancelación de ingesta en curso").
