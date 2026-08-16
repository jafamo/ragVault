## Why

Hoy no hay forma de ver, buscar ni gestionar los documentos ya ingeridos: el
usuario solo ve el estado de una subida en curso o los errores agregados en
Estadísticas, pero no un listado completo con título, tipo, tamaño, tags,
ruta y estado, ni manera de eliminar un documento. Se necesita una
"Biblioteca de documentos" como tercera vista del menú (junto a Estadísticas
y Chats) que dé visibilidad y control total sobre el corpus indexado.

## What Changes

- Nueva vista "Biblioteca" en el menú de vistas (`AccountMenu`), junto a
  "Chats" y "Estadísticas", que activa un tercer estado en `viewStore`
  (`"chat" | "stats" | "library"`).
- Nuevo componente `DocumentLibrary` con una tabla estilo datatable:
  columnas Estado, Título, Tipo/Formato, Tamaño, Tags, Ruta absoluta, y
  columna de acciones con botón Eliminar.
- Buscador/filtro independiente por cada columna (texto libre en
  título/tipo/tags/ruta, selector para Estado).
- Nuevo endpoint `GET /documents` que devuelve el listado completo de
  documentos (no solo el objeto individual de `/documents/{id}/status`) con
  los campos necesarios para la tabla.
- Nuevo endpoint `DELETE /documents/{id}` que elimina el documento: sus
  chunks/embeddings del vector store, su fila en SQL (y relaciones
  `document_tags`) y el fichero físico en disco.
- **BREAKING**: el modelo `Document` añade los campos `size_bytes: int` y
  `absolute_path: str`, obligatorios para documentos nuevos. Documentos ya
  ingeridos antes de este change no tendrán estos valores (requiere
  migración con backfill o valor por defecto — se detalla en design.md).

## Capabilities

### New Capabilities
- `document-library`: vista de biblioteca de documentos (tabla filtrable,
  ruta absoluta, tamaño, eliminar documento) y los endpoints
  `GET /documents` / `DELETE /documents/{id}` que la sustentan.

### Modified Capabilities
- `document-ingestion`: el modelo `Document` incorpora `size_bytes` y
  `absolute_path` como parte del contrato de datos persistido durante la
  ingesta (hoy no se guardan).

## Impact

- Backend: `backend/app/models/entities.py` (modelo `Document`), migración
  Alembic nueva, `backend/app/repositories/document_repo.py` (añadir
  `list_all`/`delete`), `backend/app/api/routes/documents.py` (nuevos
  endpoints), `backend/app/models/schemas.py` (nuevo `DocumentListItem` o
  ampliar `DocumentResponse`), pipeline de ingesta (guardar tamaño y ruta al
  crear el `Document`).
- Frontend: `frontend/src/stores/viewStore.ts`, `frontend/src/App.tsx`,
  `frontend/src/components/Layout/AccountMenu.tsx`, nuevo directorio
  `frontend/src/components/Documents/` con `DocumentLibrary.tsx` y su tabla,
  nuevo servicio en `frontend/src/services/` para consumir los endpoints.
- Sin dependencias externas nuevas; se reutiliza el patrón Repository ya
  existente y ChromaDB/SQLite tal como están.
