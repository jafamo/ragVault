---
name: ragvault-pattern-review
description: Revisa el código cambiado (diff actual o rama feature/*) contra las reglas de arquitectura, patrones de diseño y contratos de datos obligatorios de RagVault descritos en CLAUDE.md y rag_vault_plan.md. Úsala después de un /opsx:apply, antes de un `git flow feature finish`, o cuando el usuario pida "revisa los patrones" / "revisa que cumple la arquitectura".
---

Revisión de conformidad arquitectónica para RagVault. Esta skill NO busca bugs
genéricos (para eso está `/code-review`) — comprueba específicamente que el
código nuevo respeta las decisiones de diseño ya tomadas para este proyecto,
documentadas en `CLAUDE.md` y `rag_vault_plan.md`.

**Alcance**: solo los ficheros tocados en el diff actual (`git diff` contra
`develop`, o `git diff HEAD` si no hay rama base clara). No audites el
repo completo salvo que el usuario lo pida explícitamente.

## Checklist

Para cada fichero cambiado, comprueba lo que aplique según su carpeta:

**Document loaders** (`document_processing/loaders/`, `loader_factory.py`)
- Cada formato implementa una interfaz común (Strategy) — no debe haber un
  loader con lógica condicional por tipo de fichero dentro de sí mismo.
- La elección de loader por extensión vive solo en `loader_factory.py`
  (Factory Method) — ninguna ruta de API ni otro módulo debe instanciar
  loaders directamente ni hacer `if ext == ...`.

**Acceso a datos** (cualquier fichero fuera de `repositories/`)
- Ninguna ruta de API (`api/routes/`) ni servicio de dominio accede
  directamente a ChromaDB/FAISS o ejecuta queries SQL/SQLAlchemy — todo pasa
  por `repositories/vector_store.py`, `document_repo.py`, `tag_repo.py` o
  `chat_history.py` (Repository pattern).

**Auto-Tagger** (`auto_tagger.py` y quien lo invoque)
- Se implementa como un paso que envuelve la ingesta sin modificar los
  loaders existentes (Decorator), no como lógica insertada dentro de cada
  loader.
- El prompt enviado al LLM incluye siempre `existing_tags` (tags ya
  existentes en el sistema) — si no los pasa, es un bug de diseño: provoca
  proliferación de sinónimos (motivo documentado en el plan §7.5).
- Tags normalizados: minúsculas, sin acentos, máximo 5.

**Progreso de ingesta**
- Las notificaciones de estado al frontend están desacopladas del
  procesamiento en sí (Observer) — no deben mezclarse con la lógica de
  loaders/splitters/embeddings.

**Endpoints de API** (`api/routes/`)
- Actúan como Facade: orquestan llamadas al domain layer, no contienen
  lógica de LangChain, splitting, prompts ni acceso a vector store inline.

**Contrato de `sources` en `ChatMessage`**
- Si se modifica la estructura del JSON de `sources` (`chunks_used`,
  `retriever_config`), verifica que `frontend/src/components/Chat/SourcesCited.tsx`
  (o su equivalente) se actualiza en el mismo change. Si no se actualiza,
  repórtalo como hallazgo bloqueante.

**Logging**
- No hay `print()` ni `logging` estándar sin estructurar — todo pasa por
  `structlog` con `JSONRenderer`, a stdout (nunca a fichero local).
- Ningún log de nivel `info`/`warning`/`error` incluye contenido completo de
  prompts o respuestas del LLM ni secretos — eso, si hace falta, solo a
  `debug`.
- Si el código añade un nuevo punto de entrada HTTP o de procesamiento
  relevante para trazabilidad (ingesta, consulta RAG), debe propagar
  `request_id`/`session_id`/`document_id` en los logs, no solo el mensaje.

**Configuración / Ollama**
- No hay URLs de Ollama ni nombres de modelo hardcodeados fuera de
  `core/config.py` (`Settings` de pydantic-settings).
- Nada en el código intenta levantar, instalar o gestionar el contenedor de
  Ollama — solo se conecta vía `OLLAMA_BASE_URL`.

**LLMs externos**
- No se añade ninguna dependencia de API de LLM externa (OpenAI, Anthropic,
  etc.) como obligatoria. Si aparece, es un hallazgo bloqueante salvo que el
  usuario haya confirmado explícitamente esa integración.

**Trazabilidad OpenSpec / Git Flow**
- El código cambiado corresponde a un change existente en
  `openspec/changes/<nombre>/` con `tasks.md`. Si no hay change asociado
  (salvo fix trivial de una línea), repórtalo como hallazgo.
- Si se está revisando una rama, su nombre (`feature/<nombre>`) coincide con
  el nombre del change de OpenSpec.

## Cómo reportar

1. Ejecuta `git diff` (o `git diff develop...HEAD` si existe esa rama) para
   ver el alcance real del cambio. Si no hay repo git todavía, pide al
   usuario los ficheros a revisar.
2. Lee los ficheros cambiados completos (no solo el diff) cuando necesites
   contexto para juzgar un patrón — un diff aislado puede ocultar si la
   lógica ya vive en el sitio correcto.
3. Para cada incumplimiento encontrado, reporta: fichero, línea aproximada,
   qué regla de la checklist incumple, y la corrección concreta sugerida
   (no genérica).
4. No reportes como hallazgo una decisión de diseño que no esté en esta
   checklist ni en `CLAUDE.md` — esta skill no es una revisión de estilo ni
   de bugs generales.
5. Si todo cumple, dilo brevemente en una frase — no generes un informe
   largo cuando no hay hallazgos.
