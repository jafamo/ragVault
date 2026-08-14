## MODIFIED Requirements

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
