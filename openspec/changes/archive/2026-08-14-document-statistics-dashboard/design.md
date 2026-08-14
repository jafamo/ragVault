## Context

`Document` (`backend/app/models/entities.py`) ya persiste `format`,
`status`, `error_message` y `uploaded_at`, gestionados por
`DocumentRepository` (una sesión SQLAlchemy corta por método, sin ORM
compartido entre requests). No existe modelo de tags: `TagFilter.tsx`
en el frontend es un filtro sobre datos mock. El frontend no tiene
router (`chat-ui-shell` es un layout único con `Header` + `Sidebar` +
panel central) ni librería de gráficos.

## Goals / Non-Goals

**Goals:**
- Exponer, sin tocar el pipeline de ingesta, agregaciones de solo
  lectura sobre `documents` (por formato, estado y franja temporal).
- Introducir el modelo mínimo de tags para poder agregar por
  tag/temática y mostrarlo en el dashboard.
- Alternar chat ↔ estadísticas dentro del layout existente, sin router.

**Non-Goals:**
- Auto-tagging por LLM (fase posterior del plan, `rag_vault_plan.md`
  §7.5) — aquí los tags se crean/asignan manualmente vía API; el
  auto-tagger, cuando exista, reutilizará el mismo modelo.
- Estadísticas en tiempo real/streaming (SSE); el dashboard consulta
  bajo demanda al abrirse, sin polling continuo.
- Paginación o filtrado avanzado del listado de documentos con error
  (el dashboard lista todos; si el volumen crece, se revisita en un
  change posterior).

## Decisions

- **Modelo de tags mínimo**: tabla `tags` (`id`, `name` único) y tabla
  de asociación `document_tags` (`document_id`, `tag_id`), M:N vía
  `relationship` de SQLAlchemy. Alternativa descartada: campo
  `tags: str` (CSV) en `Document` — rechazada porque impide agregar
  eficientemente por tag y porque el auto-tagger futuro necesita tags
  como entidades con nombre único (evitar sinónimos duplicados, ya
  documentado en `rag_vault_plan.md`).
- **Repository nuevo (`StatsRepository`) en vez de extender
  `DocumentRepository`**: las agregaciones son consultas de solo
  lectura con propósito distinto (dashboards) al CRUD transaccional de
  documentos; mantenerlas separadas evita que `DocumentRepository`
  crezca con lógica de agregación no relacionada con el ciclo de vida
  de un documento.
- **Agregación en SQL (`GROUP BY`) vía SQLAlchemy, no en Python**: con
  SQLite el volumen esperado es bajo, pero agregar en la query evita
  cargar todos los documentos en memoria para cada refresco del
  dashboard y es el patrón ya usado (Repository sobre SQLAlchemy).
- **Franjas de tiempo como parámetro fijo del backend** (`5, 15, 30,
  90, 365` días), no configurable por el usuario en esta iteración —
  simplifica el endpoint (`GET /stats/timeline`) a devolver directamente
  los 5 buckets sin necesitar querystring; si se pide otra granularidad
  se añade en un change posterior.
- **Vista de estadísticas como toggle in-place, no ruta**: no hay
  router instalado y el layout actual (`Header`/`Sidebar` fijos,
  panel central intercambiable) ya se presta a sustituir el contenido
  central por estado de Zustand, igual que `skin`/`mode` en
  `themeStore`. Añadir React Router solo para esta vista sería
  desproporcionado.
- **Recharts** para los gráficos: componentes React declarativos,
  fácil de themear para los dos skins (Ledger/Terminal) y los dos
  modos (claro/oscuro) ya existentes vía CSS variables, sin necesitar
  manipular canvas/SVG a bajo nivel como con Chart.js o visx.
- **Tags asignables manualmente en esta iteración**: endpoint
  `POST /documents/{id}/tags` acepta una lista de nombres de tag,
  creando los que no existan (evita depender del auto-tagger para
  poder probar/usar la agregación por tag desde ya).

## Risks / Trade-offs

- [Documentos sin tag no aparecen en la distribución por tag y podrían
  confundirse con "0 documentos"] → el endpoint `/stats/tags` incluye
  explícitamente un bucket `"sin_tag"` con el recuento de documentos
  sin ninguna asociación.
- [Introducir `recharts` añade peso al bundle de frontend] →
  aceptable: es la única dependencia nueva de la vista de
  estadísticas y no se importa en el bundle del chat (import
  perezoso/`lazy` del componente `Stats`).
- [Cambiar el modelo de datos (`tags`, `document_tags`) requiere
  migración] → usar Alembic como ya indica el stack del proyecto;
  migración aditiva (nuevas tablas), sin tocar `documents`, así que no
  hay riesgo de romper datos existentes.
- [El listado de errores puede crecer sin límite si hay muchos
  documentos fallidos] → fuera de alcance para este change (ver
  Non-Goals); documentar como seguimiento si el volumen lo justifica.

## Migration Plan

1. Migración Alembic aditiva: crea `tags` y `document_tags`.
2. Despliegue backend (nuevas rutas `/stats/*`,
   `/documents/{id}/tags`) — no rompe contratos existentes.
3. Despliegue frontend con el botón nuevo en `AccountMenu` oculto tras
   el mismo detrás de la vista de chat por defecto — no cambia el
   comportamiento actual hasta que el usuario pulsa el botón.
4. Rollback: revertir el deploy de frontend/backend; el rollback de la
   migración (`alembic downgrade`) es seguro porque las tablas nuevas
   no tienen dependientes.

## Open Questions

- Ninguna bloqueante para implementar; a revisar en una futura
  iteración: si el auto-tagger (fase posterior) debe poder invalidar o
  fusionar tags creados manualmente aquí.
