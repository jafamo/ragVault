## ADDED Requirements

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
El sistema SHALL exponer `POST /chat` que reciba una pregunta, ejecute el
pipeline RAG contra los documentos indexados y devuelva la respuesta del
LLM junto con las fuentes usadas (documento, página, score de similitud).

#### Scenario: Pregunta con documentos indexados
- **WHEN** se hace `POST /chat` con una pregunta y existen documentos
  indexados relevantes
- **THEN** la respuesta incluye el texto generado y una lista de fuentes
  con documento, página y score

#### Scenario: Sin documentos indexados
- **WHEN** se hace `POST /chat` y no hay ningún documento indexado todavía
- **THEN** la respuesta indica explícitamente que no hay documentos para
  consultar, sin inventar una respuesta ni fallar con un error 500

### Requirement: Chat de la UI conectado al pipeline real
El sistema SHALL enviar el mensaje del usuario a `POST /chat` desde la UI
de chat existente, mostrando un estado de carga mientras espera y, al
recibir respuesta, la respuesta real con sus fuentes citadas mediante el
componente `SourcesCited` ya existente.

#### Scenario: Respuesta mostrada en el hilo
- **WHEN** el backend responde con éxito a `POST /chat`
- **THEN** el hilo de la sesión activa muestra el mensaje del usuario
  seguido de la respuesta real y sus fuentes citadas
