## MODIFIED Requirements

### Requirement: Historial de sesiones editable
El sistema SHALL permitir renombrar el título de una sesión del historial
haciendo clic sobre él (cambio solo local, sin persistir en backend), y
eliminar una sesión del historial mediante un control visible al pasar el
ratón, operando sobre sesiones reales persistidas vía la API de
`chat-sessions` (`GET /sessions`, `DELETE /sessions/{id}`). El panel de
historial SHALL poder colapsarse a una tira estrecha de iconos por sesión
(sin título) mediante un control visible, y expandirse de vuelta al
listado completo; el estado colapsado/expandido persiste entre recargas de
página. En viewport móvil (≤768px de ancho) el panel SHALL colapsarse
automáticamente al cargar o al cruzar ese ancho, sin esperar a que el
usuario pulse el control.

#### Scenario: Renombrar una sesión
- **WHEN** el usuario hace clic sobre el título de una sesión, edita el
  texto y confirma (Enter o pérdida de foco)
- **THEN** el título mostrado en el historial refleja el nuevo texto

#### Scenario: Eliminar una sesión
- **WHEN** el usuario pulsa el control de eliminar sobre una fila del
  historial
- **THEN** el sistema llama a `DELETE /sessions/{id}` y esa sesión
  desaparece de la lista

#### Scenario: El historial arranca con las sesiones reales del backend
- **WHEN** el usuario carga la aplicación
- **THEN** el panel HISTORIAL muestra el resultado de `GET /sessions`
  (ordenado por más reciente primero), no datos de ejemplo

#### Scenario: Colapsar el historial
- **WHEN** el usuario pulsa el control de colapsar del panel HISTORIAL
- **THEN** el panel se reduce a una tira estrecha mostrando solo un
  icono/inicial por sesión, el área de chat ocupa el ancho liberado, y
  `TagFilter`/`UploadZone`/`AccountMenu` permanecen visibles debajo
  (simplificados a lo esencial para caber en el ancho reducido, sin
  texto cortado o desbordado)

#### Scenario: Colapso automático en móvil
- **WHEN** el usuario carga la aplicación, o redimensiona la ventana,
  con un ancho de viewport ≤768px
- **THEN** el panel de historial aparece colapsado sin que el usuario
  tenga que pulsar el control; si lo expande manualmente puede seguir
  usándolo expandido hasta el siguiente cruce de ese ancho

#### Scenario: Expandir el historial colapsado
- **WHEN** el usuario pulsa el control de expandir estando el panel
  colapsado
- **THEN** el panel vuelve a mostrar el listado completo de sesiones con
  título

#### Scenario: El estado colapsado persiste
- **WHEN** el usuario colapsa el historial y recarga la página
- **THEN** el panel se muestra colapsado al cargar, sin necesidad de
  volver a pulsar el control

### Requirement: Nueva sesión de chat vacía
El sistema SHALL ofrecer un control "Nuevo chat" en el panel de
historial, visible tanto en su estado expandido como en el colapsado, que
crea una sesión vacía vía `POST /sessions` (título "Nueva conversación"
hasta que el backend le asigne uno tras el primer mensaje) y la marca
como activa, de forma que el usuario pueda empezar una conversación sobre
un tema distinto sin reutilizar el hilo de mensajes de la sesión
anterior. Si la sesión activa ya está vacía (sin mensajes), el sistema
SHALL reutilizarla en lugar de crear una sesión duplicada.

#### Scenario: Crear una sesión nueva desde el historial expandido
- **WHEN** el usuario pulsa "Nuevo chat" estando el panel de historial
  expandido y con una sesión activa que tiene mensajes
- **THEN** el sistema llama a `POST /sessions`, la sesión creada aparece
  al principio del historial con título "Nueva conversación", se marca
  como activa, y el área de chat muestra un hilo vacío sin mensajes de la
  sesión anterior

#### Scenario: Crear una sesión nueva desde el historial colapsado
- **WHEN** el usuario pulsa el icono de "Nuevo chat" estando el panel de
  historial colapsado
- **THEN** se crea y activa la sesión nueva igual que en el modo
  expandido, y el nuevo icono de sesión aparece al principio de la tira de
  iconos

#### Scenario: Evitar sesiones vacías duplicadas
- **WHEN** el usuario pulsa "Nuevo chat" estando ya activa una sesión sin
  ningún mensaje
- **THEN** no se crea una sesión adicional (no se llama a `POST /sessions`)
  y la sesión activa vacía se mantiene tal cual

#### Scenario: El hilo de mensajes es independiente por sesión
- **WHEN** el usuario cambia entre dos sesiones distintas del historial
- **THEN** el sistema carga vía `GET /sessions/{id}/messages` únicamente
  los mensajes de la sesión seleccionada, sin mezclar contenido de otras
  sesiones

#### Scenario: Borrar la última sesión no deja el historial sin sesión activa
- **WHEN** el usuario elimina la única sesión que queda en el historial
- **THEN** el sistema crea automáticamente una sesión nueva (vía
  `POST /sessions`) y la marca como activa, en vez de dejar la aplicación
  sin ninguna sesión seleccionada

### Requirement: Chat honesto sobre ser una maqueta
El sistema SHALL permitir escribir y enviar un mensaje en el input de
chat, añadirlo al hilo de la sesión activa y enviarlo al pipeline RAG
real (`POST /chat`) con el `session_id` de la sesión activa y el modelo
seleccionado, mostrando un estado de carga mientras espera respuesta.
SHALL mostrar la respuesta real del LLM con sus fuentes citadas cuando la
petición tenga éxito, y SHALL mostrar un mensaje de error explícito, sin
inventar contenido, si el backend, el modelo elegido o Ollama no
responden — el chat nunca fabrica ni simula una respuesta.

#### Scenario: Enviar un mensaje con éxito
- **WHEN** el usuario escribe un mensaje, lo envía, y el backend responde
  con éxito a `POST /chat`
- **THEN** el mensaje aparece en el hilo como mensaje de usuario, seguido
  de la respuesta real del pipeline RAG con sus fuentes citadas y el
  nombre del modelo que respondió, y ambos quedan persistidos en la
  sesión activa

#### Scenario: Fallo del backend o de Ollama
- **WHEN** la llamada a `POST /chat` falla o el backend indica que Ollama
  no está disponible
- **THEN** el hilo muestra un mensaje de error explícito, distinguible
  visualmente de una respuesta real, sin generar contenido simulado
