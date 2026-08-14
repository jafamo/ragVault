# project-scaffolding Specification

## Purpose
TBD - created by archiving change project-bootstrap. Update Purpose after archive.
## Requirements
### Requirement: Estructura de proyecto
El sistema SHALL organizar el código en `backend/app/` y `frontend/src/`
siguiendo la estructura de directorios definida en `rag_vault_plan.md` §4,
dejando los subdirectorios de dominio (`api/routes/`, `core/`,
`document_processing/`, `repositories/`, `models/`) presentes aunque vacíos
o con solo los ficheros base de este change.

#### Scenario: Estructura mínima presente
- **WHEN** se inspecciona el repositorio tras aplicar este change
- **THEN** existen `backend/app/main.py`, `backend/app/config.py`,
  `backend/app/core/logging.py`, `backend/pyproject.toml`,
  `backend/Dockerfile`, `frontend/src/App.tsx`, `frontend/src/main.tsx` y
  `frontend/package.json`

### Requirement: Configuración centralizada
El sistema SHALL leer toda su configuración a través de una clase
`Settings` basada en `pydantic-settings`, con soporte de fichero `.env`, sin
valores de configuración hardcodeados en otros módulos.

#### Scenario: Variables de entorno de Ollama
- **WHEN** se define `OLLAMA_BASE_URL` en el entorno o en `.env`
- **THEN** `Settings().ollama_base_url` refleja ese valor sin necesidad de
  cambios de código

#### Scenario: Valores por defecto sin `.env`
- **WHEN** la aplicación arranca sin fichero `.env` presente
- **THEN** `Settings()` se instancia con los valores por defecto
  documentados (`ollama_base_url=http://host.docker.internal:11434`,
  `ollama_model=llama3.1:8b`, `log_level=INFO`) sin lanzar error

### Requirement: Backend arrancable con health check
El sistema SHALL exponer un endpoint `GET /health` que responda 200 con el
estado de la aplicación y de la conectividad con el servicio Ollama
externo, sin gestionar ni intentar levantar ese servicio.

#### Scenario: Ollama disponible
- **WHEN** se hace `GET /health` y `OLLAMA_BASE_URL` responde correctamente
- **THEN** la respuesta incluye `{"status": "ok", "ollama": "reachable"}`

#### Scenario: Ollama no disponible
- **WHEN** se hace `GET /health` y `OLLAMA_BASE_URL` no responde en menos de
  2 segundos o devuelve error
- **THEN** la respuesta sigue siendo 200 (la app en sí está sana) con
  `{"status": "ok", "ollama": "unreachable"}`, sin lanzar excepción no
  controlada

### Requirement: Backend y frontend arrancables vía Docker
El sistema SHALL poder levantarse con `docker compose up` sin necesidad de
instalar dependencias en el host, y sin definir ni gestionar el contenedor
de Ollama dentro de `docker-compose.yml`.

#### Scenario: Arranque del backend
- **WHEN** se ejecuta `docker compose up ragvault-backend`
- **THEN** el servicio queda escuchando en el puerto `8000` y
  `GET /health` responde

### Requirement: Frontend accesible vía web en el puerto 9009
El sistema SHALL exponer el frontend en el puerto `9009` del host,
mapeado al puerto interno `5173` del dev server de Vite, como único punto
de acceso web pensado para el usuario final.

#### Scenario: Acceso al frontend desde el navegador
- **WHEN** se ejecuta `docker compose up ragvault-frontend` (o `docker compose up`)
  y se navega a `http://localhost:9009`
- **THEN** se carga la página del frontend y esta muestra el resultado de
  su llamada a `GET /health` del backend

