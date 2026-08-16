## MODIFIED Requirements

### Requirement: Endpoint de chat con fuentes citadas
El sistema SHALL exponer `POST /chat` que reciba una pregunta y,
opcionalmente, un `model` de Ollama a usar en lugar del configurado por
defecto, ejecute el pipeline RAG contra los documentos indexados y
devuelva la respuesta del LLM junto con las fuentes usadas (documento,
página, score de similitud) y el modelo que generó la respuesta.

#### Scenario: Pregunta con documentos indexados
- **WHEN** se hace `POST /chat` con una pregunta y existen documentos
  indexados relevantes
- **THEN** la respuesta incluye el texto generado, una lista de fuentes
  con documento, página y score, y el modelo usado para generar

#### Scenario: Sin documentos indexados
- **WHEN** se hace `POST /chat` y no hay ningún documento indexado todavía
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

## ADDED Requirements

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
