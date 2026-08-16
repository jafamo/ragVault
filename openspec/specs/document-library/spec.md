# document-library Specification

## Purpose
TBD - created by archiving change document-library. Update Purpose after archive.

## Requirements

### Requirement: Vista de biblioteca de documentos en el menú
El sistema SHALL exponer una tercera vista "Biblioteca" seleccionable
desde el mismo control de vistas que alterna entre "Chats" y
"Estadísticas", sin introducir enrutado por URL.

#### Scenario: Cambiar a la vista de biblioteca
- **WHEN** el usuario selecciona "Biblioteca" en el selector de vistas
- **THEN** la interfaz muestra la tabla de documentos en lugar del chat o
  del dashboard de estadísticas

### Requirement: Listado completo de documentos
El sistema SHALL exponer `GET /documents` devolviendo, para cada
documento ingerido, al menos: `id`, `status`, `filename` (título),
`format`, `size_bytes`, `tags` (lista de nombres), `absolute_path` y
`uploaded_at`.

#### Scenario: Consultar el listado
- **WHEN** se hace `GET /documents`
- **THEN** la respuesta incluye una entrada por cada documento existente
  en el sistema, con estado, título, formato, tamaño, tags y ruta absoluta

### Requirement: Tabla de biblioteca con filtro por columna
El sistema SHALL mostrar los documentos en una tabla con un control de
búsqueda/filtro independiente para cada columna (Estado, Título,
Tipo/Formato, Tamaño, Tags, Ruta absoluta), aplicando los filtros de forma
combinada (AND) sobre el listado obtenido de `GET /documents`.

#### Scenario: Filtrar por estado
- **WHEN** el usuario selecciona el estado "error" en el filtro de la
  columna Estado
- **THEN** la tabla solo muestra documentos cuyo `status` es `"error"`

#### Scenario: Combinar varios filtros
- **WHEN** el usuario escribe un texto en el filtro de Título y
  selecciona un tag en el filtro de Tags
- **THEN** la tabla muestra solo los documentos que cumplen ambas
  condiciones a la vez

### Requirement: Eliminación de un documento
El sistema SHALL exponer `DELETE /documents/{id}` que borra los chunks
del documento en el vector store, el fichero físico en disco (si existe)
y su registro en SQL (incluidas sus relaciones con tags). Si el documento
está `status="processing"`, el sistema SHALL cancelar primero la ingesta
en curso antes de proceder con el borrado, en vez de rechazar la
operación.

#### Scenario: Eliminar un documento existente
- **WHEN** se hace `DELETE /documents/{id}` sobre un documento con
  `status` distinto de `"processing"`
- **THEN** el documento deja de aparecer en `GET /documents`, sus chunks
  dejan de ser recuperables por `VectorStoreRepository.similarity_search`
  y el fichero físico correspondiente se elimina del disco

#### Scenario: Eliminar un documento en procesamiento (cancelación)
- **WHEN** se hace `DELETE /documents/{id}` sobre un documento con
  `status="processing"`
- **THEN** el sistema señala la cancelación de la ingesta en curso, y una
  vez que el pipeline la reconoce (o transcurre el tiempo máximo de
  espera), procede a borrar sus chunks del vector store, el fichero físico
  y su fila en SQL, sin dejar el documento en estado `error`

### Requirement: Botón de eliminar en la tabla
El sistema SHALL mostrar en cada fila de la tabla de biblioteca un botón
"Eliminar" que, tras confirmación explícita del usuario, invoca
`DELETE /documents/{id}` y retira la fila de la tabla si la operación
tiene éxito.

#### Scenario: Eliminar desde la UI
- **WHEN** el usuario pulsa "Eliminar" en una fila y confirma la acción
- **THEN** se llama a `DELETE /documents/{id}` y, si responde con éxito,
  la fila desaparece de la tabla sin recargar toda la página

#### Scenario: Cancelar la confirmación
- **WHEN** el usuario pulsa "Eliminar" en una fila pero cancela el
  diálogo de confirmación
- **THEN** no se realiza ninguna llamada a la API y la fila permanece en
  la tabla

### Requirement: Apertura del fichero original desde la tabla
El sistema SHALL exponer `GET /documents/{id}/file`, que sirve el
contenido del fichero original del documento con su tipo MIME inferido
por extensión, devolviendo `404` si el documento no existe, no tiene
`absolute_path` registrado, o el fichero ya no está presente en disco. La
tabla de biblioteca SHALL mostrar un botón "Abrir" por fila, deshabilitado
cuando `absolute_path` es `null`, que abre dicho endpoint en una pestaña
nueva.

#### Scenario: Abrir un documento con fichero disponible
- **WHEN** el usuario pulsa "Abrir" en una fila cuyo documento tiene
  `absolute_path` no nulo
- **THEN** se abre una pestaña nueva apuntando a
  `GET /documents/{id}/file`, que devuelve el contenido del fichero con el
  tipo MIME correspondiente a su formato

#### Scenario: Documento sin fichero físico asociado
- **WHEN** el documento de una fila tiene `absolute_path` nulo (p. ej. por
  backfill de un documento migrado cuyo fichero original ya no existe)
- **THEN** el botón "Abrir" de esa fila aparece deshabilitado

#### Scenario: Fichero desaparecido del disco
- **WHEN** se hace `GET /documents/{id}/file` sobre un documento con
  `absolute_path` no nulo pero cuyo fichero ya no existe en disco
- **THEN** el sistema responde `404`
