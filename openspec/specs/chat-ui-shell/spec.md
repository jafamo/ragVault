# chat-ui-shell Specification

## Purpose
TBD - created by archiving change chat-ui-shell. Update Purpose after archive.
## Requirements
### Requirement: Selector de identidad visual
El sistema SHALL ofrecer un control (desplegable) que permita cambiar
entre las identidades visuales "Ledger" y "Terminal" sin recargar la
página, aplicando la identidad elegida a toda la interfaz de chat.

#### Scenario: Cambiar de Ledger a Terminal
- **WHEN** el usuario selecciona "Terminal" en el desplegable de diseño
  estando en "Ledger"
- **THEN** la interfaz completa (cabecera, historial, chat, menú de
  cuenta) adopta inmediatamente la tipografía, colores y componentes de
  Terminal, sin recargar la página

### Requirement: Tema claro/oscuro independiente del diseño
El sistema SHALL ofrecer un control de tema claro/oscuro que funcione con
cualquiera de las dos identidades visuales, cambiando la paleta de esa
identidad sin alterar cuál está seleccionada.

#### Scenario: Alternar tema en Ledger
- **WHEN** el usuario activa "Oscuro" estando en la identidad Ledger
- **THEN** Ledger cambia a su paleta oscura (verde/cian sobre fondo tinta)
  manteniendo la identidad Ledger activa

#### Scenario: Alternar tema en Terminal
- **WHEN** el usuario activa "Claro" estando en la identidad Terminal
- **THEN** Terminal cambia a su paleta clara (ámbar/cian oscurecidos sobre
  fondo papel) manteniendo la identidad Terminal activa

### Requirement: Historial de sesiones editable
El sistema SHALL permitir renombrar el título de una sesión del historial
haciendo clic sobre él, y eliminar una sesión del historial mediante un
control visible al pasar el ratón, operando sobre los datos de ejemplo en
memoria.

#### Scenario: Renombrar una sesión
- **WHEN** el usuario hace clic sobre el título de una sesión, edita el
  texto y confirma (Enter o pérdida de foco)
- **THEN** el título mostrado en el historial refleja el nuevo texto

#### Scenario: Eliminar una sesión
- **WHEN** el usuario pulsa el control de eliminar sobre una fila del
  historial
- **THEN** esa sesión desaparece de la lista

### Requirement: Menú de cuenta con nombre de usuario
El sistema SHALL mostrar, en el punto donde antes había un rótulo genérico
de "Ajustes", el nombre del usuario logueado como control que abre un
menú con: selector de tema, selector de modelo y acción de cerrar sesión.

#### Scenario: Abrir el menú de cuenta
- **WHEN** el usuario hace clic sobre su nombre en la barra lateral
- **THEN** se despliega un panel con el tema actual, el modelo
  seleccionado y un botón "Cerrar sesión"

#### Scenario: Cerrar sesión es un stub visual
- **WHEN** el usuario pulsa "Cerrar sesión"
- **THEN** el botón muestra una confirmación visual temporal, sin
  redirigir ni invalidar ninguna sesión real (no existe autenticación en
  este change)

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
chat, añadiéndolo al hilo de la sesión activa, y SHALL responder con un
mensaje de marcador de posición visualmente distinguible de una respuesta
real, sin generar ni simular contenido de un LLM.

#### Scenario: Enviar un mensaje
- **WHEN** el usuario escribe un mensaje y lo envía
- **THEN** el mensaje aparece en el hilo como mensaje de usuario, seguido
  de un mensaje de sistema que indica explícitamente que no hay pipeline
  RAG conectado todavía

### Requirement: Health check integrado en la cabecera
El sistema SHALL seguir realizando la llamada real a `GET /health` del
backend y mostrar su resultado (estado de la app y de Ollama) en la
cabecera de la aplicación, en ambas identidades visuales.

#### Scenario: Ollama alcanzable
- **WHEN** `GET /health` responde `{"status":"ok","ollama":"reachable"}`
- **THEN** la cabecera muestra un indicador de estado positivo junto al
  nombre del modelo activo

