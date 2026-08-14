## MODIFIED Requirements

### Requirement: Menú de cuenta con nombre de usuario
El sistema SHALL mostrar, en el punto donde antes había un rótulo genérico
de "Ajustes", el nombre del usuario logueado como control que abre un
menú con: selector de identidad visual (diseño), selector de tema,
selector de modelo, control para alternar la vista principal entre chat
y estadísticas, y acción de cerrar sesión.

#### Scenario: Abrir el menú de cuenta
- **WHEN** el usuario hace clic sobre su nombre en la barra lateral
- **THEN** se despliega un panel con el diseño actual, el tema actual, el
  modelo seleccionado, el control de vista (chat/estadísticas) y un botón
  "Cerrar sesión"

#### Scenario: Cerrar sesión es un stub visual
- **WHEN** el usuario pulsa "Cerrar sesión"
- **THEN** el botón muestra una confirmación visual temporal, sin
  redirigir ni invalidar ninguna sesión real (no existe autenticación en
  este change)

#### Scenario: Alternar a la vista de estadísticas
- **WHEN** el usuario activa el control de vista de estadísticas desde el
  menú de cuenta
- **THEN** el panel central del layout (Header y Sidebar se mantienen)
  sustituye la conversación de chat por el dashboard de estadísticas, sin
  navegar a una URL distinta

#### Scenario: Volver a la vista de chat
- **WHEN** el usuario, estando en la vista de estadísticas, activa de
  nuevo el control de vista hacia "chat"
- **THEN** el panel central vuelve a mostrar la conversación de chat tal
  y como estaba antes de cambiar de vista
