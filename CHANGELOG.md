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

### Changed

- El chat de la UI deja de mostrar un mensaje de maqueta y llama al
  pipeline RAG real, con estado de carga y de error explícito
  (`rag-pipeline-basico`).

### Fixed

### Removed
