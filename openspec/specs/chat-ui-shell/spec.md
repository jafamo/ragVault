# chat-ui-shell Specification

## Purpose
TBD - created by archiving change chat-ui-shell. Update Purpose after archive.
## Requirements
### Requirement: Selector de identidad visual
El sistema SHALL ofrecer un control (desplegable) que permita cambiar
entre las identidades visuales "Ledger" y "Terminal" sin recargar la
página, aplicando la identidad elegida a toda la interfaz de chat. Este
control vive en el menú de Ajustes (`AccountMenu`), no en la cabecera.

#### Scenario: Cambiar de Ledger a Terminal
- **WHEN** el usuario abre Ajustes y selecciona "Terminal" estando en
  "Ledger"
- **THEN** la interfaz completa (cabecera, historial, chat, menú de
  cuenta) adopta inmediatamente la tipografía, colores y componentes de
  Terminal, sin recargar la página

### Requirement: Tema claro/oscuro independiente del diseño
El sistema SHALL ofrecer un control de tema claro/oscuro que funcione con
cualquiera de las dos identidades visuales, cambiando la paleta de esa
identidad sin alterar cuál está seleccionada. La cabecera SHALL mostrar
únicamente un icono único (sol/luna) que alterna entre claro y oscuro;
el control con ambas opciones explícitas ("Claro"/"Oscuro") vive en
Ajustes.

#### Scenario: Alternar tema en Ledger
- **WHEN** el usuario activa "Oscuro" estando en la identidad Ledger
- **THEN** Ledger cambia a su paleta oscura (verde/cian sobre fondo tinta)
  manteniendo la identidad Ledger activa

#### Scenario: Alternar tema en Terminal
- **WHEN** el usuario activa "Claro" estando en la identidad Terminal
- **THEN** Terminal cambia a su paleta clara (ámbar/cian oscurecidos sobre
  fondo papel) manteniendo la identidad Terminal activa

#### Scenario: Icono único en la cabecera
- **WHEN** el usuario pulsa el icono de tema en la cabecera
- **THEN** el tema alterna entre claro y oscuro sin mostrar botones
  separados "Claro"/"Oscuro" en la cabecera

### Requirement: Historial de sesiones editable
El sistema SHALL permitir renombrar el título de una sesión del historial
haciendo clic sobre él, y eliminar una sesión del historial mediante un
control visible al pasar el ratón, operando sobre los datos de ejemplo en
memoria. El panel de historial SHALL poder colapsarse a una tira estrecha
de iconos por sesión (sin título) mediante un control visible, y
expandirse de vuelta al listado completo; el estado colapsado/expandido
persiste entre recargas de página. En viewport móvil (≤768px de ancho)
el panel SHALL colapsarse automáticamente al cargar o al cruzar ese
ancho, sin esperar a que el usuario pulse el control.

#### Scenario: Renombrar una sesión
- **WHEN** el usuario hace clic sobre el título de una sesión, edita el
  texto y confirma (Enter o pérdida de foco)
- **THEN** el título mostrado en el historial refleja el nuevo texto

#### Scenario: Eliminar una sesión
- **WHEN** el usuario pulsa el control de eliminar sobre una fila del
  historial
- **THEN** esa sesión desaparece de la lista

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
  título y categoría

#### Scenario: El estado colapsado persiste
- **WHEN** el usuario colapsa el historial y recarga la página
- **THEN** el panel se muestra colapsado al cargar, sin necesidad de
  volver a pulsar el control

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

### Requirement: Selector de modelo con lista estática
El sistema SHALL mostrar en el menú de cuenta un selector con los modelos
Ollama conocidos en el momento de este change, sin consultar ningún
endpoint (no existe todavía).

#### Scenario: Modelos disponibles listados
- **WHEN** el usuario abre el selector de modelo
- **THEN** ve al menos `qwen2.5:14b` (preseleccionado), `llama3.1:8b` y
  `mistral:7b-instruct` entre las opciones

### Requirement: Chat honesto sobre ser una maqueta
El sistema SHALL permitir escribir y enviar un mensaje en el input de
chat, añadirlo al hilo de la sesión activa y enviarlo al pipeline RAG
real (`POST /chat`), mostrando un estado de carga mientras espera
respuesta. SHALL mostrar la respuesta real del LLM con sus fuentes
citadas cuando la petición tenga éxito, y SHALL mostrar un mensaje de
error explícito, sin inventar contenido, si el backend o Ollama no
responden — el chat nunca fabrica ni simula una respuesta.

#### Scenario: Enviar un mensaje con éxito
- **WHEN** el usuario escribe un mensaje, lo envía, y el backend responde
  con éxito a `POST /chat`
- **THEN** el mensaje aparece en el hilo como mensaje de usuario, seguido
  de la respuesta real del pipeline RAG con sus fuentes citadas

#### Scenario: Fallo del backend o de Ollama
- **WHEN** la llamada a `POST /chat` falla o el backend indica que Ollama
  no está disponible
- **THEN** el hilo muestra un mensaje de error explícito, distinguible
  visualmente de una respuesta real, sin generar contenido simulado

### Requirement: Health check integrado en la cabecera
El sistema SHALL seguir realizando la llamada real a `GET /health` del
backend y mostrar su resultado (estado de la app y de Ollama) en la
cabecera de la aplicación, en ambas identidades visuales.

#### Scenario: Ollama alcanzable
- **WHEN** `GET /health` responde `{"status":"ok","ollama":"reachable"}`
- **THEN** la cabecera muestra un indicador de estado positivo junto al
  nombre del modelo activo

