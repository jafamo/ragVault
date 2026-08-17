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
RAG contra los documentos indexados y devuelva la respuesta del LLM como
un stream de eventos `text/event-stream` (SSE): eventos `chunk` con
fragmentos de texto a medida que el LLM los genera, seguidos de un único
evento final `done` con las fuentes usadas (documento, página, score de
similitud) y el modelo que generó la respuesta. El sistema SHALL persistir
en la sesión indicada tanto el mensaje del usuario como la respuesta del
asistente, con sus fuentes, como parte de la misma petición, persistiendo
la respuesta del asistente únicamente si el stream se completa con éxito.

#### Scenario: Pregunta con documentos indexados
- **WHEN** se hace `POST /chat` con una pregunta, un `session_id` válido y
  existen documentos indexados relevantes
- **THEN** el cliente recibe una respuesta `text/event-stream` con uno o
  más eventos `chunk` cuyo texto concatenado forma la respuesta completa,
  seguidos de un evento `done` con la lista de fuentes (documento, página,
  score) y el modelo usado para generar

#### Scenario: Sin documentos indexados
- **WHEN** se hace `POST /chat` con un `session_id` válido y no hay ningún
  documento indexado todavía
- **THEN** el stream indica explícitamente, en su contenido, que no hay
  documentos para consultar, sin inventar una respuesta ni fallar con un
  error 500

#### Scenario: Falla la recuperación de documentos
- **WHEN** se hace `POST /chat` con un `session_id` válido y la
  recuperación contra el vector store falla (p. ej. ChromaDB no
  disponible)
- **THEN** el sistema responde con un error 5xx explícito antes de abrir
  el stream SSE, sin persistir ningún mensaje de asistente ni emitir
  eventos `chunk`/`done`

#### Scenario: Petición con modelo explícito
- **WHEN** se hace `POST /chat` incluyendo `model` con el nombre de un
  modelo Ollama disponible
- **THEN** la generación usa ese modelo en lugar de
  `Settings.ollama_model`, y el evento `done` lo refleja en su campo
  `model`

#### Scenario: Petición sin modelo explícito
- **WHEN** se hace `POST /chat` sin incluir `model`
- **THEN** la generación usa `Settings.ollama_model` como hasta ahora, sin
  cambio de comportamiento para consumidores existentes del endpoint

#### Scenario: Petición sin session_id es rechazada
- **WHEN** se hace `POST /chat` sin `session_id` o con uno que no
  corresponde a ninguna sesión existente
- **THEN** el sistema responde con un error 4xx explícito antes de abrir
  el stream, sin ejecutar el pipeline ni persistir ningún mensaje

#### Scenario: El turno de la conversación queda persistido
- **WHEN** el stream de `POST /chat` se completa con éxito (llega el
  evento `done`)
- **THEN** la sesión indicada contiene, al recuperar sus mensajes vía
  `GET /sessions/{id}/messages`, tanto el mensaje de usuario como la
  respuesta del asistente con sus fuentes y el modelo usado

#### Scenario: El LLM falla a mitad de generación
- **WHEN** Ollama deja de responder o lanza un error después de haber
  emitido ya uno o más eventos `chunk`
- **THEN** el sistema emite un evento `error` con un mensaje descriptivo y
  cierra el stream, sin persistir ninguna respuesta de asistente parcial
  en la sesión (el mensaje de usuario ya persistido se mantiene)

#### Scenario: El cliente se desconecta a mitad de stream
- **WHEN** el cliente cierra la conexión (navega fuera, cierra la
  pestaña) antes de que el stream termine
- **THEN** el sistema detiene la generación en curso contra Ollama en
  cuanto detecta la desconexión, sin seguir consumiendo tokens para nadie,
  y no persiste una respuesta de asistente parcial

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

### Requirement: Chat de la UI conectada al pipeline real
El sistema SHALL enviar el mensaje del usuario a `POST /chat` desde la UI
de chat existente, consumiendo el stream `text/event-stream` de la
respuesta y renderizando el contenido del mensaje del asistente de forma
incremental a medida que llegan eventos `chunk`, y al recibir el evento
`done`, mostrando las fuentes citadas mediante el componente
`SourcesCited` ya existente. Cada mensaje del hilo SHALL mostrar su fecha
y hora reales (no un texto de relleno) desde el momento en que aparece en
el hilo, en formato `dd/mm HH:mm`. El mensaje del asistente SHALL mostrar
además, una vez completada la respuesta, la duración transcurrida desde
que se envió la pregunta hasta que el stream terminó.

#### Scenario: Respuesta mostrada incrementalmente en el hilo
- **WHEN** el backend empieza a emitir eventos `chunk` para `POST /chat`
- **THEN** el hilo de la sesión activa muestra el mensaje del usuario
  seguido del texto del asistente creciendo progresivamente a medida que
  llegan chunks, sin esperar a que el stream termine para mostrar el
  primer texto

#### Scenario: Fuentes mostradas al terminar el stream
- **WHEN** el backend emite el evento `done` para `POST /chat`
- **THEN** el mensaje del asistente en el hilo queda fijado con su texto
  final y muestra sus fuentes citadas mediante `SourcesCited`

#### Scenario: Error mid-stream mostrado al usuario
- **WHEN** el backend emite un evento `error` para `POST /chat`
- **THEN** la UI muestra un estado de error visible en el mensaje del
  asistente en curso, en vez de dejarlo con el texto parcial como si fuera
  la respuesta completa

#### Scenario: Fecha y hora reales desde el envío
- **WHEN** el usuario envía una pregunta
- **THEN** tanto el mensaje del usuario como el mensaje del asistente
  (todavía vacío, en streaming) muestran su fecha y hora reales en el
  hilo, sin ningún texto de relleno tipo "ahora"

#### Scenario: Duración mostrada al completar la respuesta
- **WHEN** el stream de `POST /chat` se completa con éxito (llega el
  evento `done`)
- **THEN** el metadato del mensaje del asistente muestra, junto al
  modelo y la hora, la duración transcurrida desde que se envió la
  pregunta hasta ese momento

#### Scenario: Sin cronómetro en vivo durante el streaming
- **WHEN** el mensaje del asistente sigue recibiendo eventos `chunk` sin
  haber llegado aún `done`
- **THEN** su metadato no muestra ninguna duración parcial ni un
  cronómetro actualizándose en vivo

#### Scenario: Duración recalculada al recargar la página
- **WHEN** el usuario recarga la página y la sesión activa carga sus
  mensajes vía `GET /sessions/{id}/messages`
- **THEN** cada mensaje de asistente muestra la misma duración que se
  vio en el momento de generarse, calculada a partir de la diferencia
  entre su `created_at` y el `created_at` del mensaje de usuario
  inmediatamente anterior en esa sesión

