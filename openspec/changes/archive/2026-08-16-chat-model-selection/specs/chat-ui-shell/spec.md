## MODIFIED Requirements

### Requirement: Selector de modelo con lista real de Ollama
El sistema SHALL mostrar en el menú de cuenta un selector con los modelos
de generación realmente instalados en el Ollama configurado (excluyendo el
modelo de embeddings), consultados vía `GET /models`, con el modelo por
defecto del backend preseleccionado.

#### Scenario: Modelos disponibles listados
- **WHEN** el usuario abre el selector de modelo
- **THEN** ve los modelos que `GET /models` reporta como disponibles, sin
  incluir el modelo de embeddings configurado

#### Scenario: Ollama no disponible al listar modelos
- **WHEN** `GET /models` falla porque Ollama no responde
- **THEN** el selector muestra al menos el modelo por defecto configurado
  en el backend, sin bloquear el resto del menú de ajustes

### Requirement: Selección de modelo con efecto real
El sistema SHALL usar el modelo elegido en el selector para las siguientes
peticiones de chat del usuario, en memoria mientras dure la pestaña (sin
persistir entre recargas de página).

#### Scenario: Cambiar de modelo y preguntar
- **WHEN** el usuario elige un modelo distinto en el selector y envía un
  mensaje de chat
- **THEN** `POST /chat` se envía con ese modelo, y la respuesta mostrada en
  el hilo indica que fue generada por el modelo elegido

#### Scenario: Recargar la página reinicia la selección
- **WHEN** el usuario recarga la página tras haber elegido un modelo
  distinto del por defecto
- **THEN** el selector vuelve a mostrar el modelo por defecto del backend,
  no el que había elegido antes de recargar

### Requirement: Chat honesto sobre ser una maqueta
El sistema SHALL permitir escribir y enviar un mensaje en el input de
chat, añadirlo al hilo de la sesión activa y enviarlo al pipeline RAG
real (`POST /chat`) con el modelo seleccionado, mostrando un estado de
carga mientras espera respuesta. SHALL mostrar la respuesta real del LLM
con sus fuentes citadas cuando la petición tenga éxito, y SHALL mostrar un
mensaje de error explícito, sin inventar contenido, si el backend, el
modelo elegido o Ollama no responden — el chat nunca fabrica ni simula una
respuesta.

#### Scenario: Enviar un mensaje con éxito
- **WHEN** el usuario escribe un mensaje, lo envía, y el backend responde
  con éxito a `POST /chat`
- **THEN** el mensaje aparece en el hilo como mensaje de usuario, seguido
  de la respuesta real del pipeline RAG con sus fuentes citadas y el
  nombre del modelo que respondió

#### Scenario: Fallo del backend o de Ollama
- **WHEN** la llamada a `POST /chat` falla o el backend indica que Ollama
  no está disponible
- **THEN** el hilo muestra un mensaje de error explícito, distinguible
  visualmente de una respuesta real, sin generar contenido simulado
