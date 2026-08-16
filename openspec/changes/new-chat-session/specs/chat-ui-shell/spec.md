## ADDED Requirements

### Requirement: Nueva sesión de chat vacía
El sistema SHALL ofrecer un control "Nuevo chat" en el panel de
historial, visible tanto en su estado expandido como en el colapsado, que
crea una sesión vacía (sin mensajes, sin tag, título "Nueva conversación")
y la marca como activa, de forma que el usuario pueda empezar una
conversación sobre un tema distinto sin reutilizar el hilo de mensajes de
la sesión anterior. Si la sesión activa ya está vacía (sin mensajes), el
sistema SHALL reutilizarla en lugar de crear una sesión duplicada.

#### Scenario: Crear una sesión nueva desde el historial expandido
- **WHEN** el usuario pulsa "Nuevo chat" estando el panel de historial
  expandido y con una sesión activa que tiene mensajes
- **THEN** aparece una sesión nueva al principio del historial con título
  "Nueva conversación", se marca como activa, y el área de chat muestra un
  hilo vacío sin mensajes de la sesión anterior

#### Scenario: Crear una sesión nueva desde el historial colapsado
- **WHEN** el usuario pulsa el icono de "Nuevo chat" estando el panel de
  historial colapsado
- **THEN** se crea y activa la sesión nueva igual que en el modo
  expandido, y el nuevo icono de sesión aparece al principio de la tira de
  iconos

#### Scenario: Evitar sesiones vacías duplicadas
- **WHEN** el usuario pulsa "Nuevo chat" estando ya activa una sesión sin
  ningún mensaje
- **THEN** no se crea una sesión adicional y la sesión activa vacía se
  mantiene tal cual

#### Scenario: El hilo de mensajes es independiente por sesión
- **WHEN** el usuario cambia entre dos sesiones distintas del historial
- **THEN** cada una muestra únicamente los mensajes que se han enviado en
  esa sesión, sin mezclar contenido de otras sesiones

#### Scenario: Borrar la última sesión no deja el historial sin sesión activa
- **WHEN** el usuario elimina la única sesión que queda en el historial
- **THEN** el sistema crea automáticamente una sesión nueva y vacía y la
  marca como activa, en vez de dejar la aplicación sin ninguna sesión
  seleccionada
