## ADDED Requirements

### Requirement: Agregación de documentos por formato
El sistema SHALL exponer `GET /stats/by-format`, que devuelve el
recuento de documentos agrupado por `format`, calculado en la base de
datos (no en memoria) a partir de la tabla `documents`.

#### Scenario: Consultar recuento por formato
- **WHEN** se hace `GET /stats/by-format`
- **THEN** la respuesta incluye, para cada `format` presente en
  `documents`, el número de documentos con ese formato

### Requirement: Agregación de documentos por estado
El sistema SHALL exponer `GET /stats/by-status`, que devuelve el
recuento de documentos agrupado por `status` (`queued`, `processing`,
`done`, `error`), incluyendo explícitamente los estados sin ningún
documento asociado con recuento `0`.

#### Scenario: Consultar documentos pendientes de procesar
- **WHEN** se hace `GET /stats/by-status`
- **THEN** la respuesta incluye el número de documentos en
  `status="queued"` y en `status="processing"` por separado

### Requirement: Listado de documentos con error
El sistema SHALL exponer `GET /stats/errors`, que devuelve, para cada
documento con `status="error"`, su `id`, `filename`, `format` y
`error_message`.

#### Scenario: Consultar documentos fallidos
- **WHEN** se hace `GET /stats/errors`
- **THEN** la respuesta incluye un elemento por cada documento con
  `status="error"`, con su `error_message` legible

### Requirement: Agregación de documentos por franja temporal
El sistema SHALL exponer `GET /stats/timeline`, que devuelve el número
de documentos cuyo `uploaded_at` cae dentro de cada una de las
siguientes franjas relativas al instante de la consulta: últimos 5,
15, 30, 90 y 365 días. Cada franja SHALL contar todos los documentos
subidos desde su límite inferior hasta el momento de la consulta
(franjas acumulativas, no exclusivas entre sí).

#### Scenario: Consultar documentos ingeridos recientemente
- **WHEN** se hace `GET /stats/timeline`
- **THEN** la respuesta incluye un recuento para cada franja (5, 15,
  30, 90, 365 días), reflejando cuántos documentos tienen
  `uploaded_at` dentro de esa franja

### Requirement: Agregación de documentos por tag
El sistema SHALL exponer `GET /stats/by-tag`, que devuelve el número
de documentos asociados a cada tag existente, más un bucket
`"sin_tag"` con el número de documentos sin ninguna asociación en
`document_tags`.

#### Scenario: Consultar distribución por tag
- **WHEN** se hace `GET /stats/by-tag`
- **THEN** la respuesta incluye, para cada tag con al menos un
  documento asociado, su nombre y el número de documentos, y un
  elemento adicional `"sin_tag"` con el número de documentos sin tags

### Requirement: Dashboard de estadísticas en la UI
El sistema SHALL mostrar, en la vista de estadísticas, gráficos para
cada una de las agregaciones anteriores (por formato, por estado, por
franja temporal, por tag) y una tabla con el listado de documentos con
error y su `error_message`.

#### Scenario: Abrir el dashboard
- **WHEN** el usuario activa la vista de estadísticas
- **THEN** la UI consulta `/stats/by-format`, `/stats/by-status`,
  `/stats/errors`, `/stats/timeline` y `/stats/by-tag`, y renderiza un
  gráfico o tabla por cada respuesta

#### Scenario: Sin documentos con error
- **WHEN** `GET /stats/errors` devuelve una lista vacía
- **THEN** el dashboard muestra un estado vacío indicando que no hay
  documentos con error, sin mostrar una tabla vacía sin contexto
