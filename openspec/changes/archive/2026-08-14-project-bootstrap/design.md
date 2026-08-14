## Context

Este change es la base sobre la que se apoyarán todos los demás. No hay
código previo, así que las decisiones aquí fijan convenciones (estructura
de carpetas, logging, config) que el resto de changes deben seguir sin
volver a discutirlas. Restricciones ya fijadas en `CLAUDE.md` y
`rag_vault_plan.md`, no abiertas a discusión en este design:

- Ollama es un servicio externo ya desplegado; no se gestiona desde este
  repo, solo se consume vía `OLLAMA_BASE_URL`.
- El stack ELK es externo; la app solo debe loguear JSON estructurado a
  stdout.
- Patrones de diseño obligatorios para capas de dominio (Strategy,
  Repository, Decorator, Observer, Facade) — no aplican todavía en este
  change porque no hay lógica de negocio, pero la estructura de carpetas
  debe dejar sitio para ellos según `rag_vault_plan.md` §4.

## Goals / Non-Goals

**Goals:**
- Backend arrancable con `uvicorn` sirviendo `GET /health`, que a su vez
  compruebe conectividad con Ollama.
- Logging estructurado funcionando desde el primer request.
- `docker compose up ragvault-backend` funcional sin tocar nada del contenedor de
  Ollama externo.
- Estructura de carpetas que no haya que reorganizar cuando lleguen los
  changes de ingesta/RAG.

**Non-Goals:**
- Ninguna lógica de negocio (loaders, RAG, tags, sesiones).
- Frontend funcional más allá de una página que confirme que el backend
  responde — sin UI de chat todavía.
- Base de datos relacional ni vector store (llegan con
  `rag-pipeline-basico`).
- CI/CD (Fase 4 del plan).

## Decisions

**1. `structlog` sobre `python-json-logger`**
`structlog` permite bind de contexto (`request_id`, etc.) de forma nativa
sin manipular `LogRecord`, y su `JSONRenderer` cubre el requisito de
`CLAUDE.md` sin código adicional. Alternativa considerada:
`logging` + `python-json-logger` — descartada por requerir más boilerplate
para propagar contexto por request.

**2. `request_id` vía middleware ASGI, no vía `contextvars` manual disperso**
Un único middleware en `main.py` genera un `uuid4` por request, lo mete en
`structlog.contextvars` al inicio y lo limpia al final. Cualquier log
emitido durante ese request (en cualquier módulo) lo hereda automáticamente
sin pasarlo explícitamente. Evita tener que enhebrar `request_id` a mano
por cada función según vayan creciendo los siguientes changes.

**3. Health check de Ollama es una llamada HTTP simple, no un cliente
LangChain**
`GET /health` hace un `GET {OLLAMA_BASE_URL}/api/tags` con `httpx` y timeout
corto (2s). No se integra LangChain todavía (eso es de `rag-pipeline-basico`)
para no acoplar el bootstrap a una dependencia que este change no necesita.

**4. `pyproject.toml` con solo las dependencias de este alcance**
Se listan únicamente `fastapi`, `uvicorn[standard]`, `pydantic-settings`,
`structlog`, `httpx` y sus dev-deps (`pytest`, `pytest-asyncio`, `httpx`,
`ruff`, `mypy`). El resto de `rag_vault_plan.md` §8 (langchain, chromadb,
sentence-transformers, loaders...) se añade en `rag-pipeline-basico` para
que ese change sea el que realmente los introduce y se pueda auditar qué
change trajo cada dependencia pesada.

**5. Frontend con Vite + React + TypeScript, sin Tailwind/Zustand todavía**
Solo lo mínimo para que el dev server sirva una página que haga `fetch` a
`/health` y muestre el resultado. Tailwind/Zustand se añaden cuando exista
UI real que los necesite (evita dependencias sin usar en el bootstrap).

**6. Puerto web-facing fijado en 9009 para el frontend**
El acceso vía navegador al frontend se expone en el host como `9009`,
mapeado al puerto interno `5173` del dev server de Vite
(`ports: "9009:5173"` en `docker-compose.yml`). El backend sigue en `8000`,
pensado para consumo por el frontend y llamadas directas de desarrollo, no
como puerto web-facing principal. Decisión explícita del usuario, no
derivada de convención de Vite/FastAPI.

## Risks / Trade-offs

- [Riesgo] El health check a Ollama puede dar falso negativo si Ollama
  tarda en arrancar tras un reinicio del host → Mitigación: timeout corto y
  respuesta clara (`{"ollama": "unreachable"}`) en vez de que `/health`
  falle con 500; no es responsabilidad de este repo reiniciar Ollama.
- [Riesgo] Fijar la estructura de carpetas ahora, sin lógica de negocio
  real todavía, puede quedar desalineada cuando `rag-pipeline-basico`
  necesite ajustar algo → Mitigación: la estructura sigue literalmente
  `rag_vault_plan.md` §4, que ya fue diseñada pensando en las fases
  siguientes; si hace falta un ajuste se documenta como spec delta en ese
  change, no se improvisa aquí.
- [Trade-off] No incluir Tailwind/Zustand desde ya significa un pequeño
  rework de `package.json` en el siguiente change de frontend, a cambio de
  no cargar dependencias sin uso en este bootstrap.

## Migration Plan

No aplica — no hay estado previo que migrar. Despliegue: `docker compose up
ragvault-backend` tras este change deja el backend escuchando en `:8000` con
`/health` operativo. Rollback: al no tocar datos ni estado persistente,
revertir es simplemente volver al commit anterior de `feature/project-bootstrap`.

## Open Questions

- ¿SQLite se crea ya en este change (fichero vacío) o se deja completamente
  para `rag-pipeline-basico`, que es quien primero necesita persistir algo
  (documentos)? Propuesta: dejarlo para ese change, ya que aquí no hay
  ningún modelo que persistir todavía.
