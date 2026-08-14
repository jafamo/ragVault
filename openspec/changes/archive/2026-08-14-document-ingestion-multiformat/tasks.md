## 1. Dependencias

- [x] 1.1 Añadir `python-docx`, `openpyxl`, `odfpy`, `python-pptx` a
      `dependencies` en `backend/pyproject.toml`
- [x] 1.2 Añadir `libreoffice-impress` al `backend/Dockerfile` (paquete
      mínimo, no la suite completa) para la conversión de `.ppt` legacy
- [x] 1.3 Sincronizar el entorno (`uv sync` o equivalente) y confirmar
      que todos los loaders nuevos importan correctamente en el venv del
      backend

## 2. Modelo de datos

- [x] 2.1 Añadir columnas `status` (`queued`/`processing`/`done`/`error`,
      default `"queued"`) y `error_message` (nullable) a `Document` en
      `app/models/entities.py`
- [x] 2.2 Actualizar `DocumentRepository`: método `create()` ya no recibe
      `chunk_count` final (se actualiza al terminar), y nuevo método
      `update_status(document_id, status, chunk_count=None,
      error_message=None)`
- [x] 2.3 Borrar `data/ragvault.db` en desarrollo tras el cambio de
      esquema (no hay Alembic — ver design.md "Migration Plan")
- [x] 2.4 Añadir `ingestion_max_retries: int = 3` a `Settings`
      (`app/config.py`) — env var `INGESTION_MAX_RETRIES` — y su entrada
      correspondiente en `.env.example`

## 3. Loaders nuevos — formatos Office/OpenDocument ligeros

- [x] 3.1 `loaders/docx_loader.py`: `DocxLoader` sobre `python-docx`,
      iterando `document.paragraphs` **y** `document.tables` (filas con
      celdas unidas por ` | `) para no perder texto de tablas embebidas
- [x] 3.2 `loaders/text_loader.py`: `TextLoader` propio para `.md`/`.txt`
      sobre `langchain_community.document_loaders.TextLoader`
- [x] 3.3 `loaders/csv_loader.py`: `CSVLoader` propio sobre
      `langchain_community.document_loaders.csv_loader.CSVLoader`
- [x] 3.4 `loaders/excel_loader.py`: `ExcelLoader` propio sobre
      `openpyxl.load_workbook(path, data_only=True)` (valores calculados,
      no fórmulas), un `Document` por hoja con metadata `sheet_name`
- [x] 3.5 `loaders/odt_loader.py`: `OdtLoader` sobre `odfpy`
      (`odf.opendocument.load` + nodos `odf.text.P`/`H` **y**
      `odf.table.Table` embebidas, mismo formato fila/celda que 3.1)
- [x] 3.6 `loaders/ods_loader.py`: `OdsLoader` sobre `odfpy`
      (`odf.table`), un `Document` por hoja, análogo a `ExcelLoader`
- [x] 3.7 `loaders/pptx_loader.py`: `PptxLoader` sobre `python-pptx`, un
      `Document` por diapositiva con metadata `slide_number`

## 4. Loader .ppt legacy (LibreOffice)

- [x] 4.1 `loaders/ppt_legacy_loader.py`: `PptLegacyLoader` que ejecuta
      `soffice --headless --convert-to pptx --outdir <tmp> <path>` vía
      `subprocess.run` (timeout explícito) y delega en `PptxLoader` sobre
      el fichero convertido
- [x] 4.2 Limpiar el fichero `.pptx` temporal generado por la conversión
      tras procesarlo (éxito o error)
- [x] 4.3 Verificar en `docker compose exec ragvault-backend soffice
      --version` que el binario está disponible tras el build

## 5. Manejo de errores por formato

- [x] 5.1 `loaders/base.py`: definir `LoaderParsingError(format, detail)`
- [x] 5.2 Cada loader nuevo captura las excepciones específicas de su
      librería (`zipfile.BadZipFile`, `openpyxl.utils.exceptions.
      InvalidFileException`, `subprocess.CalledProcessError`, XML
      inválido en odfpy, fichero vacío) y las re-lanza como
      `LoaderParsingError`
- [x] 5.3 El pipeline de ingesta captura `LoaderParsingError` y marca
      `status="error"` con `error_message` legible; cualquier otra
      excepción no prevista se captura como fallback, se loguea con
      traceback (`level=error`) y también marca `status="error"` con un
      mensaje genérico (sin exponer el traceback)

## 6. Registro en el Factory

- [x] 6.1 Registrar `.docx`, `.odt`, `.xlsx`, `.ods`, `.csv`, `.md`,
      `.txt`, `.pptx`, `.ppt` en `_LOADERS` dentro de
      `app/document_processing/loader_factory.py`
- [x] 6.2 Confirmar que `UnsupportedFormatError.supported` refleja la
      lista completa y actualizada de extensiones

## 7. Pipeline de ingesta asíncrono

- [x] 7.1 Extraer a `app/document_processing/ingestion_pipeline.py::
      run_ingestion(document_id, path, filename)` la lógica hoy inline
      en `/upload` (carga → chunking → embeddings → indexado)
- [x] 7.2 `app/core/progress.py`: `IngestionProgressTracker` (Observer,
      dict en memoria + `threading.Lock`) con `start`, `update(stage,
      percent)`, `complete`, `fail`
- [x] 7.3 `run_ingestion` llama al tracker en cada etapa (`loading` 25%,
      `chunking` 50%, `embedding` 50-95% proporcional a chunks
      procesados, `indexing` 100%) y actualiza `DocumentRepository`
      (`status`, `chunk_count`, `error_message`) al terminar o fallar
- [x] 7.3b Envolver la llamada de embeddings con reintentos
      (`Settings.ingestion_max_retries`, backoff `1s/2s/4s`); solo ese
      paso se reintenta, no los errores de parsing
- [x] 7.4 `app/api/routes/documents.py`: `POST /upload` guarda el
      fichero, crea el documento con `status="queued"`, encola
      `run_ingestion` vía `BackgroundTasks` y devuelve `202` con la
      metadata inicial
- [x] 7.5 Nuevo `GET /documents/{id}/status`: combina `status`/
      `error_message` persistidos con `stage`/`percent` del tracker en
      memoria (si existen)

## 8. Frontend

- [x] 8.1 `services/api.ts`: reescribir `uploadDocument` sobre
      `XMLHttpRequest` con callback `onUploadProgress(percent)`; nuevo
      `getDocumentStatus(id)` para el polling
- [x] 8.2 `UploadZone.tsx`: ampliar `accept` e input validation a
      `.pdf,.docx,.odt,.xlsx,.ods,.csv,.md,.txt,.pptx,.ppt`
- [x] 8.3 `UploadZone.tsx`: estado con dos progresos independientes
      (`uploadPercent`, `parsePercent`/`parseStage`); tras el `202`,
      arrancar polling a `getDocumentStatus` cada ~1s hasta
      `done`/`error`, sin bloquear el resto de la UI
- [x] 8.4 Mostrar `error_message` del backend cuando `status === "error"`
      (incluye errores 415 de formato no soportado y errores de parsing
      específicos por formato)

## 9. Tests

- [x] 9.1 Fixtures de fichero de ejemplo por formato en
      `backend/tests/fixtures/` (`.docx`, `.odt`, `.xlsx`, `.ods`,
      `.csv`, `.md`, `.txt`, `.pptx`, `.ppt`) incluyendo variantes
      corruptas para los tests de error. `valid.ppt` se generó
      convirtiendo `valid.pptx` con el `soffice` real dentro del
      contenedor backend (no hay LibreOffice en el venv de desarrollo);
      su ruta de *error* se cubre además en `test_ppt_legacy_loader.py`
      mockeando `subprocess.run`, para que ese test no dependa de tener
      LibreOffice instalado en CI/dev
- [x] 9.2 `test_loader_factory.py`: extender a los 9 loaders nuevos y al
      error 415 con la lista completa de formatos
- [x] 9.3 Test unitario por loader nuevo: `load()` devuelve `Document`s
      con el texto esperado del fixture
- [x] 9.4 Test de fichero corrupto/vacío por formato: el loader lanza
      `LoaderParsingError` con el formato identificado
- [x] 9.5 Test del pipeline (`run_ingestion`): transición de estados
      `queued → processing → done`, y `queued → processing → error` con
      `error_message` poblado ante un `LoaderParsingError`
- [x] 9.6 Test de `IngestionProgressTracker`: `update`/`complete`/`fail`
      reflejados correctamente en lecturas concurrentes
- [x] 9.6b Test de reintentos: embeddings falla transitoriamente <
      `INGESTION_MAX_RETRIES` veces y termina en `done`; falla siempre y
      termina en `error` tras agotar los intentos configurados
- [x] 9.6c Test unitario de `DocxLoader`/`OdtLoader` con fixture que
      incluya una tabla embebida: el texto de las celdas aparece en el
      `Document` resultante
- [x] 9.7 `test_upload_route.py`: `POST /upload` devuelve `202` con
      `status: "queued"`; `GET /documents/{id}/status` refleja el
      progreso y el estado final tras completar `run_ingestion`
      síncronamente en el test (sin depender de background real)

## 10. Revisión final

- [x] 10.1 Ejecutar la skill `ragvault-pattern-review` sobre el diff
      antes de `git flow feature finish`
- [x] 10.2 `docker compose up -d --build` y subir manualmente un fichero
      de cada formato nuevo (incluyendo `.ppt` legacy) desde la UI,
      verificando ambas barras de progreso y el resultado final
      (verificado vía API directa contra Ollama real en `zeus`; detectó y
      corrigió un agotamiento del connection pool de SQLAlchemy por
      sesiones sin cerrar en `DocumentRepository`, expuesto por el
      polling de `GET /documents/{id}/status`)
