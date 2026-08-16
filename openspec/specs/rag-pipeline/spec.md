# rag-pipeline Specification

## Purpose
TBD - created by archiving change rag-pipeline-basico. Update Purpose after archive.
## Requirements
### Requirement: Pipeline de recuperación y generación desacoplado
El sistema SHALL resolver una pregunta mediante una secuencia de pasos
desacoplados (recuperar chunks relevantes → construir prompt → generar
respuesta), cada uno testable de forma independiente, en vez de lógica
monolítica en la ruta de API.

#### Scenario: Ejecución completa del pipeline
- **WHEN** se invoca el pipeline con una pregunta
- **THEN** se ejecutan en orden los pasos de recuperación, construcción de
  prompt y generación, y el resultado incluye tanto la respuesta como los
  chunks usados

### Requirement: Prompt reutilizado del plan
El sistema SHALL usar el `RAG_PROMPT` definido en `rag_vault_plan.md` §7.4
para construir el prompt enviado al LLM, sin crear una plantilla
alternativa.

#### Scenario: Prompt incluye contexto y pregunta
- **WHEN** se construye el prompt para una pregunta dada
- **THEN** incluye los chunks recuperados como contexto y la pregunta del
  usuario, siguiendo el formato de `RAG_PROMPT`

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

### Requirement: Listado de modelos Ollama disponibles
El sistema SHALL exponer `GET /models`, que consulta el Ollama configurado
(`Settings.ollama_base_url`) y devuelve los modelos de generación
instalados (excluyendo `Settings.ollama_embed_model`) junto con el modelo
por defecto (`Settings.ollama_model`).

#### Scenario: Consultar modelos disponibles
- **WHEN** se hace `GET /models` y Ollama responde
- **THEN** la respuesta incluye la lista de modelos instalados, sin el
  modelo de embeddings, y cuál es el modelo por defecto

#### Scenario: Ollama no disponible
- **WHEN** se hace `GET /models` y Ollama no responde
- **THEN** el sistema responde con un error controlado, sin tumbar el
  proceso

### Requirement: Chat de la UI conectado al pipeline real
El sistema SHALL enviar el mensaje del usuario a `POST /chat` desde la UI
de chat existente, mostrando un estado de carga mientras espera y, al
recibir respuesta, la respuesta real con sus fuentes citadas mediante el
componente `SourcesCited` ya existente.

#### Scenario: Respuesta mostrada en el hilo
- **WHEN** el backend responde con éxito a `POST /chat`
- **THEN** el hilo de la sesión activa muestra el mensaje del usuario
  seguido de la respuesta real y sus fuentes citadas

