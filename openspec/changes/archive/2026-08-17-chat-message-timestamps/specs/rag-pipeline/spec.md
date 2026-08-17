## MODIFIED Requirements

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
