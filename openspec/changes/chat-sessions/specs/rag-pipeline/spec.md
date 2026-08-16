## MODIFIED Requirements

### Requirement: Endpoint de chat con fuentes citadas
El sistema SHALL exponer `POST /chat` que reciba una pregunta, el
`session_id` de una sesión de chat existente y, opcionalmente, un `model`
de Ollama a usar en lugar del configurado por defecto, ejecute el pipeline
RAG contra los documentos indexados y devuelva la respuesta del LLM junto
con las fuentes usadas (documento, página, score de similitud) y el modelo
que generó la respuesta. El sistema SHALL persistir en la sesión indicada
tanto el mensaje del usuario como la respuesta del asistente, con sus
fuentes, como parte de la misma petición.

#### Scenario: Pregunta con documentos indexados
- **WHEN** se hace `POST /chat` con una pregunta, un `session_id` válido y
  existen documentos indexados relevantes
- **THEN** la respuesta incluye el texto generado, una lista de fuentes
  con documento, página y score, y el modelo usado para generar

#### Scenario: Sin documentos indexados
- **WHEN** se hace `POST /chat` con un `session_id` válido y no hay ningún
  documento indexado todavía
- **THEN** la respuesta indica explícitamente que no hay documentos para
  consultar, sin inventar una respuesta ni fallar con un error 500

#### Scenario: Petición con modelo explícito
- **WHEN** se hace `POST /chat` incluyendo `model` con el nombre de un
  modelo Ollama disponible
- **THEN** la generación usa ese modelo en lugar de
  `Settings.ollama_model`, y la respuesta lo refleja en su campo `model`

#### Scenario: Petición sin modelo explícito
- **WHEN** se hace `POST /chat` sin incluir `model`
- **THEN** la generación usa `Settings.ollama_model` como hasta ahora, sin
  cambio de comportamiento para consumidores existentes del endpoint

#### Scenario: Petición sin session_id es rechazada
- **WHEN** se hace `POST /chat` sin `session_id` o con uno que no
  corresponde a ninguna sesión existente
- **THEN** el sistema responde con un error 4xx explícito, sin ejecutar el
  pipeline ni persistir ningún mensaje

#### Scenario: El turno de la conversación queda persistido
- **WHEN** `POST /chat` responde con éxito
- **THEN** la sesión indicada contiene, al recuperar sus mensajes vía
  `GET /sessions/{id}/messages`, tanto el mensaje de usuario como la
  respuesta del asistente con sus fuentes y el modelo usado
