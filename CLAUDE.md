# RagVault

Chatbot RAG (Retrieval-Augmented Generation) de búsqueda documental: carga de
documentos multi-formato, indexación semántica con embeddings locales,
auto-tagging vía LLM, historial de chats con trazabilidad de fuentes, y
consulta conversacional — todo ejecutable 100% en local.

El plan de proyecto completo (arquitectura, fases, decisiones técnicas,
modelos de datos, prompts) vive en [rag_vault_plan.md](rag_vault_plan.md).
Consúltalo para el detalle; este fichero resume lo que hace falta para
trabajar día a día en el código.

## Estado actual

Repositorio recién inicializado — todavía no existe código, solo el plan.
La Fase 1 (MVP) descrita en el plan aún no ha comenzado. Git aún no está
inicializado; el flujo de ramas descrito abajo aplica desde el momento en
que se ejecute `git init`.

## Metodología de desarrollo: OpenSpec

Toda feature o fase del plan se desarrolla siguiendo **spec-driven
development con OpenSpec**, no directamente sobre el código. El CLI está
instalado y el proyecto ya tiene `openspec/` inicializado (`changes/` y
`specs/`), con skills y comandos de Claude Code en `.claude/skills/openspec-*`
y `.claude/commands/opsx/`.

Flujo estándar para cualquier trabajo nuevo:

1. **Proponer** — `/opsx:propose "<descripción de la feature>"` genera
   `proposal.md`, `design.md` y `tasks.md` dentro de
   `openspec/changes/<nombre-en-kebab-case>/`.
2. **Revisar** el proposal/design con el usuario antes de tocar código.
3. **Aplicar** — `/opsx:apply` implementa las tasks del change aprobado.
4. **Archivar** — `/opsx:archive` mueve el change completado a
   `openspec/changes/archive/` y sincroniza `openspec/specs/` con el estado
   final (specs vivas del sistema).
5. `/opsx:sync` y `/opsx:explore` para mantener specs alineadas con el
   código o explorar el estado actual antes de proponer algo nuevo.

**Granularidad de las specs**: una spec por capacidad/feature del sistema
(p. ej. `document-ingestion`, `rag-pipeline`, `auto-tagging`,
`chat-sessions`, `tags-api`), no una spec monolítica por fase del plan. Las
fases de `rag_vault_plan.md` §6 siguen marcando el orden y alcance temporal,
pero cada checkbox de una fase se traduce en uno o varios `openspec change`
sobre la capacidad correspondiente.

No implementes código de una feature nueva sin pasar antes por un change de
OpenSpec (`proposal.md` + `tasks.md` como mínimo). Excepción: fixes triviales
o de una línea que no cambian comportamiento ni contrato.

Tras cada `/opsx:apply` y antes de `git flow feature finish`, ejecuta la
skill `ragvault-pattern-review` (`.claude/skills/ragvault-pattern-review/`)
para verificar que el código nuevo respeta los patrones de diseño y
contratos de datos del proyecto (no sustituye a `/code-review`, que cubre
bugs y calidad general).

## Metodología de ramas: Git Flow

El proyecto usa **git flow** (rama `main` para releases estables, `develop`
como rama de integración). Prefijos estándar:

| Tipo | Prefijo | Se crea desde | Se fusiona en |
|------|---------|---------------|----------------|
| Feature | `feature/<nombre>` | `develop` | `develop` |
| Release | `release/<version>` | `develop` | `main` + `develop` |
| Hotfix | `hotfix/<nombre>` | `main` | `main` + `develop` |
| Support | `support/<nombre>` | `main` (tag) | — |

Convenciones de nombre: `feature/<nombre-del-change-openspec>` — el nombre
de la rama debe coincidir con el nombre del change en `openspec/changes/`
para que sea trazable (p. ej. change `document-ingestion-pdf` → rama
`feature/document-ingestion-pdf`).

Comandos (`git-flow` está instalado):

```bash
git flow init -d              # inicializar con defaults (main/develop, sin prefijos raros)
git flow feature start <nombre>
git flow feature finish <nombre>
git flow release start <version>
git flow release finish <version>
git flow hotfix start <nombre>
```

No se hace commit directo sobre `main` ni `develop` salvo merges de git
flow. Cada `feature/*` corresponde 1:1 a un change de OpenSpec ya aprobado;
no abras una rama feature sin su proposal correspondiente.

## Changelog

El versionado sigue [Semantic Versioning](https://semver.org/lang/es/) y el
histórico se documenta en [CHANGELOG.md](CHANGELOG.md) con formato
[Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/).

- Al fusionar un `feature/*` a `develop`, añade una entrada bajo
  `## [Sin publicar]` (categoría `Added`/`Changed`/`Fixed`/`Removed` según
  corresponda), describiendo el cambio desde la perspectiva del usuario, no
  la implementación. Usa el nombre del change de OpenSpec como referencia.
- Al ejecutar `git flow release start <version>`, renombra la sección
  `[Sin publicar]` a `[<version>] - <fecha>` y deja una nueva `[Sin publicar]`
  vacía encima.
- `<version>` sigue MAJOR.MINOR.PATCH: MAJOR para cambios incompatibles de
  API/esquema de datos, MINOR para features nuevas retrocompatibles (la
  mayoría de las fases del plan), PATCH para fixes.
- No se documentan en el changelog cambios internos sin impacto observable
  (refactors, tests, tareas de OpenSpec/tooling) salvo que el usuario lo pida.

## Stack

- **Backend**: FastAPI (async), LangChain para orquestación RAG, SQLAlchemy + Alembic.
- **LLM local**: Ollama, servido en un contenedor Docker externo ya desplegado
  (no lo levantamos nosotros). Se conecta vía `OLLAMA_BASE_URL`.
- **Embeddings**: `nomic-embed-text` (Ollama) o `sentence-transformers`
  (`all-MiniLM-L6-v2`).
- **Vector store**: ChromaDB (MVP); FAISS o pgvector como alternativas futuras.
- **Base de datos relacional**: SQLite en MVP → PostgreSQL en producción.
- **Frontend**: React + TypeScript, Tailwind CSS, Zustand, SSE para streaming
  de respuestas.
- **Logging**: `structlog`, JSON estructurado a stdout — ver sección
  "Logging (compatible con ELK)".

## Arquitectura y patrones

Capas: Frontend → API (FastAPI) → Domain (RAG pipeline, document processing,
auto-tagger) → Infrastructure (vector store, SQL, filesystem). Ver diagrama
completo en `rag_vault_plan.md` §2.

Patrones de diseño ya decididos — respétalos al añadir código nuevo:

- **Strategy** en los document loaders (uno por formato bajo interfaz común).
- **Factory Method** en `loader_factory.py` para elegir loader según extensión.
- **Chain of Responsibility** en el pipeline RAG (split → embed → retrieve → generate).
- **Repository** para abstraer el acceso a vectores (ChromaDB/FAISS) y a SQL.
- **Decorator** en el Auto-Tagger, que envuelve la ingesta sin tocar los loaders.
- **Observer** para notificar progreso de ingesta al frontend.
- **Facade** en los endpoints de la API sobre el pipeline LangChain.

## Estructura del proyecto (objetivo)

```text
backend/app/{api/routes, core, document_processing/loaders, repositories, models}
frontend/src/{components/{Chat,Sessions,Documents,Tags,Layout}, services, stores}
```

Estructura de directorios completa en `rag_vault_plan.md` §4. Al crear
ficheros nuevos, respeta esta ubicación en vez de inventar una organización
distinta.

## Fuentes de documentos futuras

`docker-compose.yml` incluye, comentado, un ejemplo de montaje SMB/NFS de un
recurso compartido de un NAS Synology como carpeta de solo lectura para
ingesta adicional de documentos. Es una mejora futura, no implementada: no
la descomentes ni la actives sin pasar antes por un `openspec change`
(sugerido: `document-source-synology`) que defina credenciales, formato de
sincronización (montaje directo vs. File Station API) y cómo se dispara la
ingesta de lo que aparezca en esa carpeta.

## Conexión a Ollama

Ollama corre en un contenedor Docker **externo e independiente**, ya
desplegado — nunca lo incluyas en `docker-compose.yml` de este proyecto ni
asumas que hay que instalarlo. Puede estar en la misma máquina
(`http://host.docker.internal:11434`, con
`extra_hosts: host.docker.internal:host-gateway` en Linux) o en otra
máquina de la LAN (URL/IP directa) — el endpoint real no está hardcodeado
en ningún fichero versionado, se configura vía `OLLAMA_BASE_URL` en `.env`
(ver `.env.example` para el valor por defecto de referencia). Igual para
`OLLAMA_MODEL`/`OLLAMA_EMBED_MODEL`: el modelo concreto en uso es una
elección de entorno, no una constante del código.

## Logging (compatible con ELK)

Ya existe un stack ELK (Elasticsearch/Logstash/Kibana) desplegado fuera de
este repo — igual que Ollama, no lo gestionamos aquí. La única
responsabilidad de la aplicación es emitir logs en un formato que ese stack
externo pueda ingerir sin trabajo adicional:

- **Formato**: JSON estructurado, un objeto por línea, siempre a **stdout**
  (nunca a fichero local) — así el shipper externo (Filebeat/Logstash) los
  recoge desde los logs del contenedor Docker sin configuración extra en
  este proyecto.
- **Librería**: `structlog` configurado con `JSONRenderer`, inicializado una
  vez en `core/logging.py` (o `app/core/logging.py` según la estructura del
  plan) y usado en vez de `print()` o `logging` estándar sin estructurar en
  todo el backend.
- **Campos obligatorios** en cada entrada: `timestamp` (ISO 8601 UTC),
  `level`, `logger`/`event`, `message`. Campos contextuales cuando apliquen:
  `request_id` (uno por request HTTP, vía middleware de FastAPI, para poder
  seguir en Kibana todo el recorrido de una consulta: embed → retrieve →
  generate), `session_id`, `document_id`.
- **Uvicorn**: sustituir el logging de acceso por defecto por uno que
  también emita JSON (no dejar el formato de texto plano de Uvicorn
  conviviendo con el resto de logs estructurados).
- **Nivel de log** configurable vía `Settings.log_level` (pydantic-settings,
  variable `LOG_LEVEL`), no hardcodeado.
- **No loguear secretos ni contenido sensible en `info`/`warning`/`error`**:
  el contenido completo de prompts/respuestas del LLM, si se necesita para
  debug, solo a nivel `debug`.
- Esto es infraestructura transversal, no una feature aislada: debe quedar
  resuelto en el primer `openspec change` de la Fase 1 (setup del proyecto),
  antes o junto con el pipeline RAG básico — el resto de changes solo deben
  añadir logs siguiendo esta convención, no reinventar el formato.

## Convenciones al implementar

- Sigue las fases del plan (`rag_vault_plan.md` §6) en orden: MVP antes que
  multi-formato/auto-tagging, antes que funcionalidades avanzadas, antes que
  producción. No adelantes trabajo de fases posteriores sin que se pida.
- Los prompts al LLM local (auto-tagging, títulos de sesión, RAG) tienen
  plantillas ya definidas en el plan (§7.4, §7.5, §7.6) — reutilízalas en
  vez de crear variantes nuevas salvo que se pida explícitamente ajustarlas.
- El auto-tagger debe recibir siempre los tags existentes en el prompt para
  evitar sinónimos duplicados (motivo documentado en el plan).
- Los `sources` de cada `ChatMessage` se persisten como JSON con
  `chunks_used` y `retriever_config` — no cambies ese contrato sin
  actualizar también el consumidor en el frontend (`SourcesCited.tsx`).
- Tests: unitarios para el pipeline y loaders; integración end-to-end se
  añaden en Fase 3.

## Qué NO hacer

- No añadir una API externa de LLM (OpenAI, Anthropic, etc.) como
  dependencia obligatoria — el proyecto debe funcionar 100% offline con
  Ollama local. Integraciones externas opcionales requieren confirmación
  explícita del usuario.
- No levantar ni gestionar el contenedor de Ollama desde este repo.
- No saltarte el Repository pattern para acceder directamente a ChromaDB o
  SQL desde rutas de la API.
