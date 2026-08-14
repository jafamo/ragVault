# document-tags Specification

## Purpose
TBD - created by archiving change document-statistics-dashboard. Update Purpose after archive.
## Requirements
### Requirement: Modelo de tags con nombre único
El sistema SHALL persistir los tags en una tabla `tags` (`id`, `name`
único) y su asociación con documentos en una tabla M:N `document_tags`
(`document_id`, `tag_id`), a través de un `TagRepository` que abstrae
el acceso SQL, sin acceso directo desde las rutas de la API.

#### Scenario: No se duplican tags por nombre
- **WHEN** se intenta crear un tag cuyo `name` ya existe (comparación
  insensible a mayúsculas/minúsculas)
- **THEN** el sistema reutiliza el tag existente en lugar de crear uno
  duplicado

### Requirement: Asignación manual de tags a un documento
El sistema SHALL exponer `POST /documents/{id}/tags`, que recibe una
lista de nombres de tag y los asocia al documento indicado, creando
los tags que no existan todavía.

#### Scenario: Asignar tags nuevos y existentes
- **WHEN** se hace `POST /documents/{id}/tags` con una lista que
  mezcla nombres de tags ya existentes y nombres nuevos
- **THEN** el documento queda asociado a todos los tags de la lista, y
  solo se crean en `tags` los nombres que no existían previamente

#### Scenario: Documento inexistente
- **WHEN** se hace `POST /documents/{id}/tags` con un `id` que no
  corresponde a ningún documento
- **THEN** el sistema responde con un error controlado (404) sin crear
  tags huérfanos

### Requirement: Listado de tags de un documento
El sistema SHALL exponer `GET /documents/{id}/tags`, que devuelve los
nombres de los tags asociados a ese documento.

#### Scenario: Consultar tags de un documento
- **WHEN** se hace `GET /documents/{id}/tags` sobre un documento con
  tags asignados
- **THEN** la respuesta incluye la lista de nombres de esos tags
