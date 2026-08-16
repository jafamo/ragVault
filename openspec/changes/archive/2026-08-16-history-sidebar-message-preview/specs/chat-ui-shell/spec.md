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
usuario pulse el control. En el estado expandido del panel, cada fila de
sesión SHALL poder expandirse individualmente (como máximo una a la vez)
para mostrar una vista previa de sus mensajes sin cambiar la sesión activa
del panel central, con un control separado dentro de esa vista previa para
activar la sesión en el panel central cuando el usuario lo decida. El
listado de sesiones SHALL desplazarse verticalmente de forma aislada del
resto del panel: `TagFilter`, `UploadZone` y `AccountMenu` permanecen
siempre visibles sin necesidad de scroll para alcanzarlos, sin que este
comportamiento sea una preferencia configurable en Ajustes.

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

#### Scenario: Previsualizar los mensajes de una sesión
- **WHEN** el usuario, con el panel HISTORIAL expandido, pulsa el
  control de vista previa de una fila de sesión
- **THEN** esa fila se expande dentro de la propia barra mostrando sus
  mensajes en orden cronológico, con los primeros 5 visibles sin scroll y
  el resto accesible desplazándose dentro de esa vista previa, sin que la
  conversación activa del panel central cambie

#### Scenario: Solo una vista previa abierta a la vez
- **WHEN** el usuario expande la vista previa de una sesión estando ya
  otra sesión con su vista previa abierta
- **THEN** la vista previa anterior se colapsa automáticamente y solo
  queda expandida la sesión recién seleccionada

#### Scenario: Activar una sesión desde su vista previa
- **WHEN** el usuario, con la vista previa de una sesión expandida, pulsa
  el control explícito para abrir esa sesión en el chat
- **THEN** esa sesión pasa a ser la sesión activa del panel central,
  mostrando su conversación completa como si se hubiera seleccionado
  directamente

#### Scenario: Colapsar el panel oculta las vistas previas
- **WHEN** el usuario colapsa el panel HISTORIAL a la tira estrecha de
  iconos estando una sesión con su vista previa expandida
- **THEN** la tira de iconos no muestra ninguna vista previa de mensajes,
  y al volver a expandir el panel las filas vuelven a su estado colapsado
  por defecto (sin vista previa abierta)

#### Scenario: El listado de sesiones se desplaza sin arrastrar el resto del panel
- **WHEN** hay suficientes sesiones para que el listado no quepa entero
  en el alto disponible del panel HISTORIAL
- **THEN** el listado de sesiones muestra su propio scroll vertical, y
  `TagFilter`, `UploadZone` y `AccountMenu` siguen visibles en su
  posición sin necesidad de desplazarse por las sesiones para llegar a
  ellos

#### Scenario: El aislamiento de scroll no es una preferencia de usuario
- **WHEN** el usuario abre el menú de Ajustes/`AccountMenu`
- **THEN** no existe ningún control para activar o desactivar el scroll
  aislado del listado de sesiones — es comportamiento de layout fijo, no
  una opción configurable
