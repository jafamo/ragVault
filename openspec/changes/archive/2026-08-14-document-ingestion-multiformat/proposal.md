## Why

RagVault solo ingiere PDFs. La Fase 2 del plan (`rag_vault_plan.md` §6)
requiere soportar los formatos de documento habituales de un vault
documental — Office, OpenDocument y texto plano — antes de abordar
auto-tagging o historial de sesiones, ya que ambos dependen de tener un
conjunto de documentos representativo. El `LoaderFactory` (Strategy +
Factory Method) ya existe para PDF desde `rag-pipeline-basico`, así que
esto es extender ese punto de extensión, no crearlo.

Además, con más formatos (algunos costosos de parsear, como Excel/
PowerPoint grandes) la ingesta síncrona actual — el usuario espera con la
petición HTTP abierta hasta que termina todo el pipeline — deja de ser
aceptable: hace falta manejo de errores específico por formato y
visibilidad de progreso, tal y como recoge la Fase 2 del plan ("Progress
bar durante la ingesta") y el patrón Observer ya reservado en `CLAUDE.md`
para "notificar progreso de ingesta al frontend".

## What Changes

- Añadir un `DocumentLoader` (Strategy) por formato nuevo: `.docx`,
  `.odt`, `.xlsx`, `.ods`, `.csv`, `.md`, `.txt`, `.pptx`, `.ppt`,
  reutilizando loaders de `langchain-community` cuando existan, o
  librerías ligeras (`python-docx`, `odfpy`, `python-pptx`) en vez de
  reimplementar parsing o arrastrar dependencias pesadas innecesarias.
  Los loaders de DOCX y ODT extraen también el texto de tablas
  embebidas (no requiere modelo — es texto estructurado), y los de
  XLSX/ODS leen valores calculados de fórmulas, no la fórmula en sí.
  Extracción/descripción de imágenes queda fuera de alcance: ninguno de
  los modelos Ollama disponibles hoy es multimodal (ver design.md).
- Registrar los nuevos loaders en `_LOADERS` dentro de
  `loader_factory.py`.
- **Manejo de errores por formato**: cada loader debe distinguir errores
  de parsing específicos de su formato (fichero corrupto, hoja vacía,
  contraseña, versión no soportada) y traducirlos a un error de ingesta
  controlado con un mensaje que identifique el formato y la causa, en vez
  de un 500 genérico.
- **Reintentos configurables**: nueva variable de entorno
  `INGESTION_MAX_RETRIES` (default `3`) que controla cuántos reintentos
  hace el pipeline ante un fallo transitorio del paso de embeddings
  (llamada a Ollama) antes de marcar el documento como `error`.
- **BREAKING**: `POST /upload` deja de ser síncrono. Pasa a devolver
  `202 Accepted` en cuanto el fichero se ha recibido y persistido,
  arrancando el resto del pipeline (parseo → chunking → embeddings →
  indexado) en segundo plano (`BackgroundTasks` de FastAPI — Celery/Redis
  es Fase 4, no se adelanta aquí). La respuesta incluye el `id` del
  documento y su `status` inicial (`"queued"`).
- **Nuevo**: tabla `documents` gana una columna `status`
  (`queued`/`processing`/`done`/`error`) y `error_message` (nullable).
- **Nuevo endpoint** `GET /documents/{id}/status`: devuelve el estado
  actual de la ingesta (`status`, `stage`, `percent`, `error_message` si
  aplica), para que el frontend haga polling mientras procesa.
- **Nuevo**: `IngestionProgressTracker` (Observer) — el pipeline de
  ingesta notifica cada etapa (carga → chunking → embeddings → indexado)
  y su progreso aproximado; el endpoint de estado lee de ahí. No modifica
  los loaders existentes más allá de que el pipeline que los invoca ahora
  emite eventos de progreso.
- **Frontend**: `UploadZone` pasa a mostrar dos barras de progreso
  independientes:
  1. **Subida** — progreso de transferencia del fichero al backend
     (bloqueante en el sentido de que es la propia petición HTTP en
     curso), vía eventos de progreso de `XMLHttpRequest`.
  2. **Parseo** — progreso del pipeline en segundo plano tras recibir el
     202, mediante polling a `GET /documents/{id}/status`; no bloquea la
     UI (el usuario puede seguir navegando/chateando mientras termina).
  Amplía además la lista de extensiones aceptadas en el selector de
  fichero y el drag-and-drop, y refleja errores específicos por formato.
- Tests unitarios por loader nuevo, por error específico de formato, y de
  la máquina de estados de `status` (`queued` → `processing` →
  `done`/`error`).

## Capabilities

### New Capabilities

(ninguna — se reutiliza la capability existente `document-ingestion`)

### Modified Capabilities

- `document-ingestion`:
  - "Selección de loader por extensión (Strategy + Factory)" pasa de
    soportar `.pdf` a soportar `.pdf`, `.docx`, `.odt`, `.xlsx`, `.ods`,
    `.csv`, `.md`, `.txt`, `.pptx`, `.ppt`.
  - "Endpoint de subida" cambia de respuesta síncrona (200 con el
    documento ya indexado) a asíncrona (202 con `status: "queued"`).
  - "Zona de subida funcional en la UI" se amplía para aceptar las
    nuevas extensiones y mostrar dos barras de progreso independientes
    (subida y parseo).
  - Nuevo requisito: manejo de errores específico por formato durante el
    parseo.
  - Nuevo requisito: seguimiento de progreso de ingesta vía
    `GET /documents/{id}/status` y notificación Observer desde el
    pipeline.

## Impact

- **Backend**: `app/document_processing/loaders/` (nuevos ficheros),
  `app/document_processing/loader_factory.py` (registro),
  `app/document_processing/ingestion_pipeline.py` (nuevo — orquesta
  carga→chunking→embeddings→indexado y emite progreso; hasta ahora esta
  lógica vivía inline en la ruta `/upload`), `app/core/progress.py`
  (nuevo — `IngestionProgressTracker`), `app/models/entities.py` +
  `app/repositories/document_repo.py` (columna `status`/`error_message`),
  `app/api/routes/documents.py` (`/upload` asíncrono +
  `GET /documents/{id}/status`), `pyproject.toml` (dependencias de
  parsing), `backend/Dockerfile` (LibreOffice headless para `.ppt`
  legacy, ver design.md).
- **Frontend**: `UploadZone.tsx`, `services/api.ts` (`uploadDocument` con
  `XMLHttpRequest` + nuevo `getDocumentStatus`).
- **Base de datos**: no hay Alembic configurado todavía en el proyecto;
  el cambio de esquema se aplica vía `Base.metadata.create_all` (ver
  design.md, "Migration Plan") — solo afecta a entornos de desarrollo sin
  datos reales.
- **Contrato**: `DocumentResponse` del `POST /upload` cambia de
  significado (documento recién creado y en cola, no ya indexado) —
  cualquier consumidor que asumiera indexado inmediato debe pasar a
  consultar `GET /documents/{id}/status`.
