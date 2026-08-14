## Why

El repositorio solo contiene el plan (`rag_vault_plan.md`) y el entorno de
IA (OpenSpec, git flow, convenciones en `CLAUDE.md`). No existe todavía
ningún esqueleto de aplicación. Antes de poder implementar ingesta de
documentos o el pipeline RAG (Fase 1 del plan) hace falta una base común:
estructura de proyecto, configuración, logging y conexión al LLM local, para
que los siguientes changes se apoyen en algo real en vez de crear cada uno
su propia convención.

## What Changes

- Crear la estructura de carpetas `backend/app/` y `frontend/src/` descrita
  en `rag_vault_plan.md` §4 (solo los directorios/ficheros base; los
  módulos de dominio como loaders, RAG pipeline o repositorios llegan en
  changes posteriores).
- FastAPI app skeleton (`main.py`) con CORS habilitado, sin endpoints de
  negocio todavía (solo `/health`).
- Configuración centralizada con `pydantic-settings`
  (`ollama_base_url`, `ollama_model`, `ollama_embed_model`, `log_level`,
  leídos de `.env`).
- Logging estructurado con `structlog` + `JSONRenderer` a stdout, con
  middleware de `request_id` por petición HTTP, según la convención de
  `CLAUDE.md` ("Logging (compatible con ELK)").
- Health check de conexión al servicio Ollama externo (`GET /health`
  comprueba que `OLLAMA_BASE_URL` responde).
- `Dockerfile` de backend y ajuste de `docker-compose.yml` (ya existe un
  esqueleto en la raíz con el placeholder de Synology comentado) para que
  levante el backend real.
- Esqueleto mínimo de frontend (`frontend/src/App.tsx`, `main.tsx`,
  `package.json`) sin componentes de negocio — solo para tener el proyecto
  arrancable.
- `pyproject.toml` de backend con las dependencias base de
  `rag_vault_plan.md` §8 necesarias para este alcance (fastapi, uvicorn,
  pydantic-settings, structlog) — el resto (langchain, chromadb, loaders...)
  se añade en el change `rag-pipeline-basico`.

Fuera de alcance (van en `rag-pipeline-basico` u otros changes futuros):
document loaders, ChromaDB, pipeline RAG, endpoints `/chat`/`/upload`,
auto-tagger, historial de sesiones, UI real de chat.

## Capabilities

### New Capabilities

- `project-scaffolding`: estructura base del proyecto (backend + frontend),
  configuración vía pydantic-settings, Dockerfile/docker-compose
  arrancables, y health check de conexión a Ollama.
- `observability-logging`: logging JSON estructurado a stdout compatible
  con el stack ELK externo, con correlación por `request_id`.

### Modified Capabilities

(ninguna — no existen specs previas en `openspec/specs/`)

## Impact

- Código nuevo: `backend/app/**`, `frontend/src/**` (esqueletos),
  `backend/Dockerfile`, `backend/pyproject.toml`.
- Ficheros existentes modificados: `docker-compose.yml` (se completa el
  servicio `ragvault-backend` ya presente, sin tocar el placeholder comentado de
  Synology).
- Dependencias externas: ninguna nueva de infraestructura — sigue
  dependiendo de Ollama y del stack ELK, ambos ya desplegados fuera de este
  repo.
- No hay cambios de esquema de datos ni de API pública todavía (no hay
  endpoints de negocio en este change).
