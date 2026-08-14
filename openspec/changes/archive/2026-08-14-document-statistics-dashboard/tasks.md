## 1. Modelo de datos (tags)

- [x] 1.1 Añadir `Tag` y tabla de asociación `document_tags` en
      `backend/app/models/entities.py` (M:N con `Document`)
- [x] 1.2 ~~Migración Alembic~~ — el repo no tiene Alembic instalado
      todavía (el esquema se crea vía `Base.metadata.create_all()` en
      `init_db()`); las tablas nuevas se crean automáticamente por el
      mismo mecanismo. Introducir Alembic queda fuera de alcance de
      este change.

## 2. Repositorios

- [x] 2.1 Crear `TagRepository` en `backend/app/repositories/tag_repo.py`
      (crear/reutilizar tag por nombre, asignar/listar tags de un
      documento)
- [x] 2.2 Crear `StatsRepository` en
      `backend/app/repositories/stats_repo.py` con las agregaciones por
      formato, estado, franja temporal y tag (todas vía `GROUP BY` en
      SQLAlchemy)

## 3. API

- [x] 3.1 `POST /documents/{id}/tags` y `GET /documents/{id}/tags`
      (404 si el documento no existe)
- [x] 3.2 `GET /stats/by-format`
- [x] 3.3 `GET /stats/by-status` (incluye estados sin documentos con
      recuento 0)
- [x] 3.4 `GET /stats/errors`
- [x] 3.5 `GET /stats/timeline` (franjas 5/15/30/90/365 días)
- [x] 3.6 `GET /stats/by-tag` (incluye bucket `"sin_tag"`)
- [x] 3.7 Logging estructurado (structlog) en las rutas nuevas,
      siguiendo la convención de `core/logging.py`

## 4. Frontend — dependencia y estado de vista

- [x] 4.1 Añadir `recharts` a `frontend/package.json`
- [x] 4.2 Añadir estado de vista activa (`chat` | `stats`) al store de
      Zustand correspondiente (nuevo o extensión de uno existente)
- [x] 4.3 Añadir control en `AccountMenu.tsx` para alternar la vista,
      con estilos consistentes con los selectores existentes
      (`settings-seg`)

## 5. Frontend — dashboard de estadísticas

- [x] 5.1 Crear `frontend/src/components/Stats/` con el layout del
      dashboard, cargado con `lazy`/`Suspense` para no incluir
      `recharts` en el bundle de la vista de chat
- [x] 5.2 Añadir llamadas a `/stats/*` en `frontend/src/services/api.ts`
- [x] 5.3 Gráfico de documentos por formato
- [x] 5.4 Gráfico/indicador de documentos pendientes de procesar
      (`queued`/`processing`)
- [x] 5.5 Tabla de documentos con error y su `error_message`, con
      estado vacío cuando no hay errores
- [x] 5.6 Gráfico de documentos por franja temporal (5/15/30/90/365
      días)
- [x] 5.7 Gráfico de distribución por tag (incluye `"sin_tag"`)
- [x] 5.8 Aplicar theming de los dos skins (Ledger/Terminal) y los dos
      modos (claro/oscuro) a los gráficos de Recharts vía las CSS
      variables ya existentes

## 6. Verificación

- [x] 6.1 Tests unitarios de `TagRepository` y `StatsRepository`
      (agregaciones, bucket `sin_tag`, franjas temporales)
- [x] 6.2 Tests de los endpoints `/stats/*` y `/documents/{id}/tags`
      (incluye caso 404)
- [x] 6.3 Ejecutar `ragvault-pattern-review` sobre el diff antes de
      `git flow feature finish` — sin hallazgos
- [x] 6.4 Probar manualmente el toggle chat ↔ estadísticas en ambos
      skins y ambos modos de color — verificado con Playwright
      (Ledger/claro y Terminal/oscuro, capturas en scratchpad)
