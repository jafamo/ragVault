## 1. Estructura backend

- [x] 1.1 Crear `backend/app/__init__.py`, `backend/app/api/__init__.py`,
      `backend/app/api/routes/` (vacío, con `.gitkeep` o primer router),
      `backend/app/core/`, `backend/app/document_processing/`,
      `backend/app/repositories/`, `backend/app/models/` según
      `rag_vault_plan.md` §4 (solo carpetas/placeholders, sin lógica de
      negocio todavía)
- [x] 1.2 Crear `backend/pyproject.toml` con dependencias mínimas:
      `fastapi`, `uvicorn[standard]`, `pydantic-settings`, `structlog`,
      `httpx`; dev: `pytest`, `pytest-asyncio`, `httpx`, `ruff`, `mypy`
- [x] 1.3 Crear `backend/tests/conftest.py` con fixture de `TestClient`

## 2. Configuración

- [x] 2.1 Implementar `backend/app/config.py` con `Settings`
      (pydantic-settings): `ollama_base_url`, `ollama_model`,
      `ollama_embed_model`, `log_level`, lectura de `.env`
- [x] 2.2 Crear `.env.example` en la raíz con las variables soportadas

## 3. Logging estructurado (observability-logging)

- [x] 3.1 Implementar `backend/app/core/logging.py`: configuración de
      `structlog` con `JSONRenderer`, timestamp ISO 8601 UTC, nivel desde
      `Settings.log_level`
- [x] 3.2 Middleware ASGI de `request_id` (uuid4 por request) en
      `main.py`, usando `structlog.contextvars`
- [x] 3.3 Reconfigurar el logging de Uvicorn (access log) para que también
      emita JSON, no el formato de texto plano por defecto
- [x] 3.4 Test: verificar que un log emitido dentro de un request incluye
      `request_id` y que es JSON parseable

## 4. FastAPI app y health check

- [x] 4.1 Implementar `backend/app/main.py`: instancia FastAPI, CORS,
      registro del middleware de logging
- [x] 4.2 Implementar `GET /health` que comprueba `OLLAMA_BASE_URL` vía
      `httpx` con timeout de 2s y devuelve `{"status": "ok", "ollama":
      "reachable"|"unreachable"}`
- [x] 4.3 Test: `/health` responde 200 tanto si Ollama está arriba como si
      no (mockeando `httpx`)

## 5. Docker

- [x] 5.1 Crear `backend/Dockerfile` (imagen Python, instala dependencias
      de `pyproject.toml`, arranca con uvicorn)
- [x] 5.2 Actualizar el servicio `ragvault-backend` en `docker-compose.yml`
      de la raíz para que apunte al `Dockerfile` real (sin tocar el bloque
      comentado del futuro montaje Synology)
- [x] 5.3 Verificar manualmente: `docker compose up ragvault-backend` y
      `curl localhost:8000/health` responde

## 6. Frontend mínimo

- [x] 6.1 Scaffold de `frontend/` con Vite + React + TypeScript
      (`package.json`, `src/main.tsx`, `src/App.tsx`), configurando el dev
      server de Vite para escuchar en `0.0.0.0:5173` dentro del contenedor
- [x] 6.2 `App.tsx` hace `fetch(VITE_API_URL + '/health')` al backend y
      muestra el resultado (sin UI de chat todavía)
- [x] 6.3 `frontend/Dockerfile` (Vite dev server, expone `5173`)
- [x] 6.4 Verificar manualmente: `docker compose up ragvault-frontend` y que
      `http://localhost:9009` carga la página y muestra el resultado de
      `/health`

## 7. Verificación final

- [x] 7.1 `openspec validate project-bootstrap` sin errores
- [x] 7.2 Ejecutar la skill `ragvault-pattern-review` sobre el diff
- [x] 7.3 `pytest` en verde en `backend/`
