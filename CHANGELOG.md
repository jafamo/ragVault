# Changelog

Todos los cambios notables de este proyecto se documentan en este fichero.

El formato se basa en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/),
y este proyecto usa [Semantic Versioning](https://semver.org/lang/es/)
(`MAJOR.MINOR.PATCH`).

## [Sin publicar]

### Added

- Esqueleto inicial del backend (FastAPI) y frontend (React + Vite), con
  `GET /health` que comprueba la conectividad con Ollama
  (`project-bootstrap`).
- Logging estructurado en JSON a stdout, correlacionado por `request_id`
  por petición, compatible con el stack ELK externo (`project-bootstrap`).
- Servicios Docker `ragvault-backend` (puerto 8000) y `ragvault-frontend`
  (puerto 9009, acceso web) (`project-bootstrap`).
- Interfaz de chat con dos identidades visuales intercambiables — Ledger
  (verde/cian) y Terminal (ámbar/cian) —, cada una con modo claro/oscuro,
  historial de sesiones editable, filtro de tags, zona de subida de
  documentos y menú de cuenta con selector de modelo Ollama
  (`chat-ui-shell`). Todavía sobre datos de ejemplo — sin conexión real al
  pipeline RAG.
- Ingesta real de PDF (`POST /upload`) y chat con RAG real contra Ollama
  (`POST /chat`): chunking, embeddings e indexación en ChromaDB, con
  fuentes citadas reales en la UI de chat (`rag-pipeline-basico`). Cierra
  el MVP de la Fase 1 del plan.
- Ingesta multi-formato: además de PDF, ahora se pueden subir documentos
  Word (`.docx`, `.odt`), hojas de cálculo (`.xlsx`, `.ods`, `.csv`),
  texto (`.md`, `.txt`) y presentaciones PowerPoint (`.pptx`, `.ppt`,
  esta última convertida internamente con LibreOffice). La subida muestra
  dos barras de progreso independientes — transferencia del fichero e
  indexado en segundo plano —, con reintentos automáticos configurables
  ante fallos transitorios y mensajes de error específicos por formato
  cuando un fichero está corrupto o no se puede parsear
  (`document-ingestion-multiformat`).
- El panel HISTORIAL de la barra lateral se puede colapsar a una tira
  estrecha de iconos por sesión, liberando ancho para el chat; en
  viewport móvil (≤768px) se colapsa automáticamente
  (`sidebar-collapse-history`).
- Vista de estadísticas, accesible desde un control en el menú de Ajustes
  que alterna entre chat y estadísticas: documentos por formato, por
  estado (pendientes/procesados/con error, con el mensaje de error de
  cada documento fallido), ingeridos por franja temporal (últimos 5, 15,
  30, 90 y 365 días) y por tag. Incluye un modelo mínimo de tags
  asignables manualmente a un documento (`document-statistics-dashboard`).
- Botón "Nuevo chat" en el panel HISTORIAL (visible también en su estado
  colapsado) para abrir una sesión vacía sin arrastrar los mensajes de la
  conversación activa; si la sesión activa ya está vacía, se reutiliza en
  vez de crear una duplicada (`new-chat-session`).
- Persistencia real del historial de chat: las sesiones y sus mensajes
  (con fuentes citadas y modelo usado) se guardan en base de datos y
  sobreviven a recargar la página, en vez de perderse al refrescar. El
  título de cada sesión se genera automáticamente con el LLM tras el
  primer mensaje (`chat-sessions`).
- Nueva vista "Biblioteca", accesible desde el mismo control del menú de
  cuenta que alterna Chat/Estadísticas: tabla de todos los documentos
  ingeridos con buscador independiente por columna (estado, título,
  tipo/formato, tamaño, tags, ruta absoluta del fichero) y botón para
  eliminar un documento, incluyendo sus chunks indexados y el fichero
  físico. Eliminar un documento que todavía se está procesando cancela su
  ingesta en curso en vez de bloquear el borrado (`document-library`).
- Vista previa de mensajes por sesión en el panel HISTORIAL: cada fila de
  sesión se puede expandir individualmente para ver sus mensajes sin
  cambiar la conversación activa del panel central, con un botón "Abrir
  en el chat" para activarla cuando se decida. El listado de sesiones
  gana además su propio scroll vertical, independiente del resto del
  panel: `TagFilter`, la zona de subida y el menú de cuenta quedan
  siempre visibles sin tener que desplazarse por las sesiones
  (`history-sidebar-message-preview`).

### Changed

- El selector de identidad visual (Ledger/Terminal) se mueve de la
  cabecera al menú de Ajustes; la cabecera pasa a mostrar solo un icono
  único para alternar entre tema claro y oscuro
  (`sidebar-collapse-history`).
- El chat de la UI deja de mostrar un mensaje de maqueta y llama al
  pipeline RAG real, con estado de carga y de error explícito
  (`rag-pipeline-basico`).
- `POST /upload` deja de esperar a que termine toda la ingesta: confirma
  la recepción del fichero al momento y procesa el resto en segundo plano
  (`document-ingestion-multiformat`).
- El selector de modelo del menú de cuenta deja de ser cosmético: consulta
  los modelos realmente instalados en el Ollama configurado (`GET
  /models`) en vez de una lista fija, y el modelo elegido se envía en cada
  mensaje del chat, que responde con el modelo que efectivamente generó
  la respuesta. La selección no persiste entre recargas de página
  (`chat-model-selection`).
- El historial de sesiones ya no arranca con conversaciones de ejemplo:
  se inicia con una única sesión nueva y vacía (`new-chat-session`).
- **BREAKING**: `POST /chat` pasa a requerir `session_id`; ya no acepta
  peticiones sin una sesión existente (`chat-sessions`).
- Los ficheros subidos ya no se borran al terminar la ingesta: se
  conservan en disco (visibles como "ruta absoluta" en la Biblioteca)
  hasta que el usuario elimina el documento explícitamente
  (`document-library`).

### Fixed

- `VITE_API_URL` del frontend ahora es configurable vía `.env` en lugar de
  estar fijado a `http://localhost:8000` en `docker-compose.yml`. Con el
  valor fijo, acceder a la UI desde otro equipo de la LAN hacía que el
  navegador intentase llamar a su propio `localhost`, mostrando "Ollama no
  disponible" y "Failed to fetch" en el chat.

### Removed

## [0.0.1] - 2026-08-14

### Fixed

- Corregido el patrón `data/` en `.gitignore`, que excluía sin querer
  `frontend/src/data/` (incluyendo `mockModels.ts`) al no estar anclado a
  la raíz del repo. Esto rompía el build de producción con Vite
  (`Failed to resolve import "../../data/mockModels"`).
