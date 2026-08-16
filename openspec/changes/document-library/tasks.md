## 1. Modelo de datos y migración

- [x] 1.1 Añadir `size_bytes: int | None` y `absolute_path: str | None` al
      modelo `Document` en `backend/app/models/entities.py`
- [x] 1.2 Generar migración Alembic (`ALTER TABLE documents ADD COLUMN
      size_bytes`, `absolute_path`, ambas nullable) — el proyecto no tiene
      Alembic realmente cableado todavía (sin `alembic.ini`/`versions/`);
      se implementó el `ALTER TABLE` idempotente equivalente en
      `DocumentRepository.init_db()`. Pendiente de sustituir por Alembic
      real en un change de infraestructura futuro.
- [x] 1.3 Backfill: no aplica un paso separado — las columnas nuevas
      quedan `NULL` para filas existentes (comportamiento documentado en
      design.md); los documentos nuevos las rellenan desde la subida
- [x] 1.4 Actualizar `DocumentRepository.create` para aceptar y persistir
      `size_bytes` y `absolute_path`

## 2. Ingesta: capturar tamaño y ruta

- [x] 2.1 En el flujo de `POST /upload`, calcular `size_bytes` (tamaño del
      fichero recibido) y `absolute_path` (ruta absoluta donde se
      persiste) antes de crear el `Document`. El fichero subido ahora se
      persiste en `settings.uploads_dir` en vez de un temporal que se
      borraba al terminar la ingesta, para que `absolute_path` sea real y
      el borrado físico en `DELETE /documents/{id}` tenga sentido.
- [x] 2.2 Actualizar tests de ingesta existentes para cubrir los nuevos
      campos (cubierto en `test_upload_route.py` y en el nuevo
      `test_document_library_routes.py`)

## 3. Backend: listado y borrado

- [x] 3.1 Crear `backend/app/core/cancellation.py` con `CancellationRegistry`
      (dict en memoria + `threading.Lock`, mismo estilo que
      `IngestionProgressTracker`): `request_cancel(document_id)`,
      `is_cancelled(document_id)`, `clear(document_id)`
- [x] 3.2 Añadir puntos de comprobación de `is_cancelled` en `run_ingestion`
      (`backend/app/document_processing/ingestion_pipeline.py`): tras el
      loader, tras el chunking y entre lotes de embeddings; al detectarla,
      dejar de escribir chunks y marcar `status="cancelled"` (no `error`)
- [x] 3.3 Añadir `DocumentRepository.list_all()` que devuelva todos los
      documentos con sus tags cargados
- [x] 3.4 Añadir `VectorStoreRepository.delete_by_document_id(id)` si no
      existe ya un método equivalente
- [x] 3.5 Añadir `DocumentRepository.delete(id)` (borra fila y relaciones
      `document_tags` vía cascade)
- [x] 3.6 Implementar `GET /documents` en
      `backend/app/api/routes/documents.py` devolviendo `DocumentListItem`
      (id, status, filename, format, size_bytes, tags, absolute_path,
      uploaded_at)
- [x] 3.7 Implementar `DELETE /documents/{id}`: si `status="processing"`,
      llamar a `cancellation_registry.request_cancel(id)` y esperar (poll
      con timeout ~5s) a que el documento salga de `processing`; en
      cualquier caso, continuar borrando vector store → fichero físico
      (best-effort con log) → fila SQL, en ese orden
- [x] 3.8 Añadir `DocumentListItem` (o ampliar `DocumentResponse`) en
      `backend/app/models/schemas.py`
- [x] 3.9 Tests de integración para `GET /documents` y
      `DELETE /documents/{id}` (caso éxito con documento `done`, caso
      cancelación de documento `processing`, caso documento inexistente)
      en `backend/tests/unit/test_document_library_routes.py`. También se
      corrigió un gap preexistente: `run_ingestion` nunca marcaba
      `status="processing"` (se quedaba en `"queued"` durante todo el
      procesado), lo que habría hecho inalcanzable la rama de cancelación
      — ahora se marca al empezar el pipeline.

## 4. Frontend: vista de biblioteca

- [x] 4.1 Añadir `"library"` a `View` en `frontend/src/stores/viewStore.ts`
- [x] 4.2 Añadir botón "Biblioteca" al grupo de vistas en
      `frontend/src/components/Layout/AccountMenu.tsx`
- [x] 4.3 Añadir rama de render lazy para `DocumentLibrary` en
      `frontend/src/App.tsx`
- [x] 4.4 Crear servicio de API (`listDocuments`, `deleteDocument`) en
      `frontend/src/services/` (añadido en `services/api.ts`, mismo
      fichero donde ya viven el resto de llamadas)
- [x] 4.5 Crear `frontend/src/components/Documents/DocumentLibrary.tsx`
      con la tabla y los filtros por columna, siguiendo el patrón de
      markup/CSS de `ErrorsTable.tsx`
- [x] 4.6 Implementar filtro combinado (AND) en cliente por Estado,
      Título, Tipo, Tamaño, Tags y Ruta absoluta
- [x] 4.7 Implementar botón "Eliminar" por fila con diálogo de
      confirmación, llamando a `deleteDocument` y retirando la fila en
      éxito
- [x] 4.8 Formatear `size_bytes` de forma legible (KB/MB) y mostrar "—"
      cuando `size_bytes`/`absolute_path` sean `null`

## 4b. Abrir fichero original desde la tabla

- [x] 4b.1 Implementar `GET /documents/{id}/file` en
      `backend/app/api/routes/documents.py`: `FileResponse` con tipo MIME
      inferido por extensión (`mimetypes`) y `Content-Disposition: inline`;
      `404` si el documento no existe, `absolute_path` es `null`, o el
      fichero no está en disco
- [x] 4b.2 Añadir botón "Abrir" por fila en `DocumentLibrary.tsx` que abre
      `GET /documents/{id}/file` en pestaña nueva; deshabilitado cuando
      `absolute_path` es `null`
- [x] 4b.3 Test de integración: documento con fichero devuelve 200 y
      contenido correcto; documento sin `absolute_path` o con fichero
      borrado devuelve 404

## 4c. Aislar los tests de la base de datos de desarrollo

- [x] 4c.1 `backend/tests/conftest.py` fija `SQLITE_PATH`,
      `CHROMA_PERSIST_DIR` y `UPLOADS_DIR` a un directorio temporal antes
      de importar `app.main` (y con ello `app.config`/`document_repo.py`,
      que crean el engine de SQLAlchemy a nivel de módulo), para que los
      tests dejen de escribir sobre `backend/data/` (la BD y el vector
      store reales de desarrollo/Docker). El directorio temporal se borra
      al terminar la sesión de tests (`pytest_sessionfinish`).
- [x] 4c.2 Fixture `autouse`/`session` que llama a `init_db()` al empezar
      la sesión: al arrancar siempre desde una BD de test vacía (en vez de
      la de desarrollo, que ya tenía tablas de ejecuciones previas), varios
      tests que instancian repositorios directamente (sin pasar por
      `client`, que dispara `init_db()` vía el lifespan) fallaban con "no
      such table" — bug preexistente que quedaba oculto mientras los tests
      corrían contra la BD de desarrollo ya inicializada.
- [x] 4c.3 Verificado que `backend/data/ragvault.db`, `data/chroma/` y
      `data/uploads/` no cambian (mismo hash MD5, mismo nº de ficheros)
      tras ejecutar `pytest` con el contenedor Docker corriendo en
      paralelo.

## 5. Verificación

- [x] 5.1 Ejecutar la skill `ragvault-pattern-review` sobre el diff antes
      de `git flow feature finish` — sin hallazgos bloqueantes (se
      corrigió un `time.sleep` en función `async` detectado por `ruff`
      durante la revisión, ver 3.7)
- [x] 5.2 Probado manualmente con backend+frontend levantados y Playwright:
      la vista "Biblioteca" se activa desde el menú de cuenta en ambos
      skins (ledger/terminal), la tabla muestra Estado/Título/Tipo/
      Tamaño/Tags/Ruta absoluta, el filtro por Estado reduce las filas
      correctamente, y "Eliminar" quita la fila tras confirmar. Se
      detectó (pre-existente, no introducido por este change) que los
      tests de backend escriben sobre la misma `data/ragvault.db` de
      desarrollo en vez de una BD aislada — deja filas de prueba
      visibles en la Biblioteca; no se corrige aquí por ser un problema
      de aislamiento de tests ya presente antes de este change.
- [x] 5.3 Añadir entrada en `CHANGELOG.md` bajo `[Sin publicar]` al
      fusionar a `develop`
