## ADDED Requirements

### Requirement: Modelo de datos de sesiones y mensajes
El sistema SHALL persistir sesiones de chat (`ChatSession`: `id`, `title`
opcional, `created_at`, `updated_at`) y sus mensajes (`ChatMessage`: `id`,
`session_id`, `role` ("user"/"assistant"), `content`, `created_at`,
`model_used` opcional, `sources` opcional) en base de datos relacional,
con relación 1:N de sesión a mensajes y borrado en cascada.

#### Scenario: Los mensajes de una sesión sobreviven a un reinicio
- **WHEN** se crea una sesión, se le añaden mensajes, y la aplicación se
  reinicia
- **THEN** `GET /sessions/{id}/messages` sigue devolviendo los mismos
  mensajes que antes del reinicio

### Requirement: API de gestión de sesiones
El sistema SHALL exponer `POST /sessions` (crea una sesión vacía),
`GET /sessions` (lista sesiones ordenadas por `updated_at` descendente),
`GET /sessions/{id}` (detalle de una sesión), `GET /sessions/{id}/messages`
(mensajes de una sesión en orden cronológico) y `DELETE /sessions/{id}`
(elimina la sesión y todos sus mensajes).

#### Scenario: Crear y listar sesiones
- **WHEN** se hace `POST /sessions` y a continuación `GET /sessions`
- **THEN** la sesión creada aparece en el listado

#### Scenario: Eliminar una sesión elimina sus mensajes
- **WHEN** se elimina una sesión que tiene mensajes vía
  `DELETE /sessions/{id}` y luego se pide `GET /sessions/{id}/messages`
- **THEN** el sistema responde que la sesión no existe (404), sin dejar
  mensajes huérfanos en la base de datos

#### Scenario: Pedir una sesión inexistente
- **WHEN** se hace `GET /sessions/{id}` con un id que no corresponde a
  ninguna sesión
- **THEN** el sistema responde con 404, no con una lista vacía ni un error
  500

### Requirement: Fuentes citadas persistidas por mensaje
El sistema SHALL persistir, para cada mensaje del asistente, las fuentes
usadas para generar la respuesta en el campo `sources` como JSON con la
forma `{"chunks_used": [...], "retriever_config": {...}}` documentada en
`CLAUDE.md`, de modo que puedan recuperarse íntegras al releer la sesión.

#### Scenario: Las fuentes se recuperan igual que se generaron
- **WHEN** un mensaje de asistente se generó citando fuentes de dos
  documentos distintos
- **THEN** `GET /sessions/{id}/messages` devuelve ese mensaje con las
  mismas fuentes (documento, página, score) en su campo `sources`

### Requirement: Título de sesión auto-generado
El sistema SHALL generar automáticamente el título de una sesión, usando
el LLM configurado, la primera vez que se procesa un mensaje de usuario en
una sesión sin título todavía. Si la generación del título falla, el
sistema SHALL continuar respondiendo al mensaje con normalidad y dejar la
sesión sin título para reintentarlo en el siguiente mensaje.

#### Scenario: Primer mensaje genera título
- **WHEN** se envía el primer mensaje de una sesión sin título
- **THEN** `GET /sessions/{id}` devuelve, tras procesar ese mensaje, un
  `title` no vacío derivado del contenido de la pregunta

#### Scenario: Mensajes siguientes no regeneran el título
- **WHEN** se envía un segundo mensaje en una sesión que ya tiene título
- **THEN** el `title` de la sesión no cambia
