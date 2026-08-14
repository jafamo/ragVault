## Context

`LoaderFactory` (`app/document_processing/loader_factory.py`) ya aplica
Strategy + Factory Method para `.pdf` vía `PDFLoader` (que envuelve
`langchain_community.document_loaders.PyPDFLoader`). El endpoint
`POST /upload` hoy ejecuta todo el pipeline (carga → chunking →
embeddings → almacenamiento) de forma síncrona dentro de la propia
petición HTTP. Con más formatos — algunos costosos de parsear — y la
necesidad de progreso visible, el pipeline pasa a ejecutarse en segundo
plano y el endpoint solo confirma la recepción del fichero.

No hay Alembic configurado en el proyecto todavía (`init_db()` usa
`Base.metadata.create_all`, sin migraciones versionadas) — es una
limitación preexistente, no algo que este change deba resolver.

## Goals / Non-Goals

**Goals:**
- Soportar `.docx`, `.odt`, `.xlsx`, `.ods`, `.csv`, `.md`, `.txt`,
  `.pptx`, `.ppt` con la misma interfaz
  `DocumentLoader.load(path) -> list[Document]`.
- Mantener las dependencias de parsing mínimas salvo donde no exista
  alternativa razonable (ver Decisión 4, `.ppt` legacy).
- Que cada loader distinga errores específicos de su formato (corrupto,
  vacío, protegido con contraseña, versión no soportada) de un error
  interno genérico, y que el pipeline los traduzca a un estado `error`
  con mensaje legible — sin tumbar el proceso ni dejar el documento en un
  estado ambiguo.
- Ingesta asíncrona con progreso observable: subida (bytes transferidos)
  y parseo (etapa del pipeline) como señales independientes.
- Reintentos automáticos configurables ante fallos transitorios del paso
  de embeddings (dependiente de red hacia Ollama).
- Extraer correctamente el texto de tablas embebidas en DOCX/ODT (no
  requiere modelo — es texto estructurado) y los valores calculados de
  fórmulas en XLSX/ODS (ya resuelto leyendo con `data_only=True`).

**Non-Goals:**
- Cola de trabajos persistente/distribuida (Celery+Redis) — es Fase 4;
  aquí basta con `BackgroundTasks` de FastAPI (un solo proceso/worker).
- Extracción/descripción de imágenes embebidas (fotos, capturas) u OCR de
  PDFs escaneados — ninguno de los modelos Ollama disponibles hoy
  (`gemma2:27b`, `qwen2.5:14b`, `deepseek-r1:14b`,
  `deepseek-coder-v2:16b`, `llama3.1:8b`, `qwen2.5-coder:7b`,
  `deepseek-r1:7b`, `qwen2.5:7b`, `mistral:7b-instruct`) es multimodal;
  requeriría pullear un modelo de visión (`llava`, `qwen2-vl`,
  `llama3.2-vision`) y sería un change aparte.
- WebSocket/SSE para progreso — se usa polling (ver Decisión 10); se
  revisita si el chat adopta SSE para streaming en un change posterior y
  conviene unificar el transporte.

## Decisions

1. **DOCX → loader propio sobre `python-docx`, no `Docx2txtLoader`.**
   `docx2txt` extrae texto de forma poco fiable cuando hay tablas
   embebidas (las celdas pueden perder separación de fila/columna).
   `python-docx` permite iterar `document.paragraphs` y `document.tables`
   explícitamente y construir un texto legible por tabla (filas con
   celdas unidas por ` | `), preservando el contenido tabular sin
   necesitar ningún modelo — es solo texto estructurado. Alternativa
   descartada: `UnstructuredWordDocumentLoader` (dependencia
   `unstructured`, pesada, innecesaria dado que `python-docx` ya resuelve
   el caso de tablas).

2. **MD y TXT → `TextLoader` (langchain-community), sin parseo de
   Markdown.** Mismo razonamiento que en 1.

3. **CSV → `CSVLoader` (langchain-community), sin dependencias nuevas**
   (stdlib `csv`). **XLSX → loader propio sobre `openpyxl`** (`data_only=True`,
   un `Document` por hoja), sin `pandas` — el proyecto no la usa en
   ningún otro punto y sería una dependencia nueva solo para esto.

4. **ODT y ODS → loaders propios sobre `odfpy`.** `odfpy` es puro Python,
   sin dependencias nativas, y cubre ambos formatos OpenDocument (Writer
   y Calc) con la misma librería — evita añadir dos dependencias
   distintas para dos formatos hermanos. `OdtLoader` extrae los nodos de
   texto (`odf.text.P`/`H`) del documento **y también** las tablas
   embebidas en el propio Writer (`odf.table.Table`, mismo tratamiento
   fila/celda que en la decisión 1 para DOCX), no solo párrafos.
   `OdsLoader` recorre hojas y celdas (`odf.table`) de forma análoga al
   `ExcelLoader` de la decisión 3 (un `Document` por hoja).

5. **PPTX → loader propio sobre `python-pptx`.** Pura Python, sin
   dependencias nativas ni `unstructured`. Extrae el texto de cada forma
   de texto (`shape.text_frame`) por diapositiva, un `Document` por
   slide con metadata `slide_number`.

6. **PPT (binario legacy, PowerPoint 97-2003) → conversión previa con
   LibreOffice headless.** No existe librería pura Python que parsee el
   formato OLE/binario de `.ppt` — `python-pptx` solo soporta `.pptx`. Se
   añade `libreoffice-impress` (paquete mínimo, no la suite completa) a
   `backend/Dockerfile` y un `PptLegacyLoader` que ejecuta
   `soffice --headless --convert-to pptx --outdir <tmp> <path>` y delega
   en el `PptxLoader` de la decisión 5 sobre el resultado. Es la única
   dependencia "pesada" que se introduce en este change — justificada
   porque es la única vía viable para ese formato sin recurrir a
   `unstructured` (que internamente hace exactamente esto mismo, pero
   arrastrando además `nltk`/`Pillow`/detección de tipo de fichero).
   Alternativa descartada: soportar solo `.pptx` y rechazar `.ppt` — se
   descarta porque el usuario ha pedido explícitamente ambos formatos de
   PowerPoint.

7. **Manejo de errores por formato.** Cada loader nuevo captura las
   excepciones específicas de su librería subyacente (p. ej.
   `zipfile.BadZipFile` en DOCX/PPTX/XLSX/ODT/ODS al ser ficheros ZIP con
   estructura interna, `openpyxl.utils.exceptions.InvalidFileException`,
   `subprocess.CalledProcessError` en la conversión LibreOffice) y las
   re-lanza como una única `LoaderParsingError(format, detail)` común,
   definida en `loaders/base.py`. El pipeline de ingesta captura
   `LoaderParsingError` y marca el documento como `status="error"` con
   `error_message` legible; cualquier otra excepción no prevista se
   captura igual como fallback pero se loguea con `level=error` y
   traceback completo para diagnóstico (no se expone el traceback al
   usuario).

8. **Reintentos configurables solo en el paso de embeddings.**
   `Settings.ingestion_max_retries: int = 3` (env var
   `INGESTION_MAX_RETRIES`, default `3`, siguiendo el patrón ya
   establecido de configuración vía `.env`/`Settings` en vez de
   constantes). Los reintentos se aplican **únicamente** a la llamada de
   embeddings contra Ollama dentro de `run_ingestion` — es el único paso
   con fallo transitorio real (red/timeout hacia un servicio externo);
   reintentar un error de parsing (`LoaderParsingError`) no tiene sentido
   porque el fichero seguiría corrupto. Backoff simple (`1s, 2s, 4s`)
   entre intentos; si se agotan los `INGESTION_MAX_RETRIES` intentos, el
   documento pasa a `status="error"` con el último error como
   `error_message`.

9. **Ingesta asíncrona con `BackgroundTasks`.** `POST /upload` guarda el
   fichero subido a disco, crea la fila `documents` con
   `status="queued"` y devuelve `202` inmediatamente. La orquestación
   completa (antes inline en la ruta) se extrae a
   `app/document_processing/ingestion_pipeline.py::run_ingestion(document_id,
   path)`, registrada vía `BackgroundTasks.add_task`. Al ser una función
   síncrona, Starlette la ejecuta en un thread del threadpool — no
   bloquea el event loop, sin necesitar Celery/Redis para esta fase.

10. **Progreso vía `IngestionProgressTracker` (Observer) + polling.**
   Tracker en memoria (`dict[document_id, IngestionProgress]` protegido
   con `threading.Lock`, dado que el pipeline corre en un thread del
   pool y el endpoint de estado en el event loop). El pipeline llama a
   `tracker.update(document_id, stage, percent)` en cada etapa (`loading`
   25%, `chunking` 50%, `embedding` 50-95% proporcional a chunks
   procesados, `indexing` 100%). `GET /documents/{id}/status` combina el
   `status` persistido (para sobrevivir a un reinicio del proceso, ya que
   perder ese dato dejaría un documento "atascado" en la UI sin
   explicación) con el detalle fino en memoria (`stage`/`percent`, que sí
   se pierde en un reinicio — aceptable, es solo feedback de progreso, no
   estado de negocio). Se prefiere polling (frontend hace `GET` cada
   ~1s mientras `status !== "done"|"error"`) a SSE/WebSocket porque el
   proyecto no tiene aún infraestructura de streaming (SSE está listada
   para el streaming del chat en Fase 2, pero no implementada todavía) —
   introducir dos mecanismos de push distintos en el mismo change sería
   sobre-ingeniería; se revisita si el chat adopta SSE.

11. **Subida con progreso vía `XMLHttpRequest`.** `fetch()` no expone
    progreso de subida de forma fiable entre navegadores; `XHR` sí vía
    `xhr.upload.onprogress`. `uploadDocument` en `services/api.ts` se
    reescribe sobre `XMLHttpRequest` envuelto en una `Promise`,
    aceptando un callback `onUploadProgress(percent)`.

## Risks / Trade-offs

- [LibreOffice headless en la imagen Docker del backend aumenta su
  tamaño de forma notable (cientos de MB)] → se instala solo
  `libreoffice-impress` (no la suite completa `libreoffice`) para acotar
  el impacto; si el tamaño de imagen se vuelve un problema real, la
  alternativa es un servicio de conversión aparte, pero no se justifica
  adelantarlo sin evidencia de que sea necesario.
- [Progreso fino en memoria se pierde si el proceso backend se reinicia
  a mitad de ingesta] → el `status` grueso persistido permite al frontend
  al menos saber que sigue "processing" en vez de mostrar un error falso;
  el usuario puede reintentar si tarda demasiado.
- [`BackgroundTasks` en un solo proceso no escala a ingestas concurrentes
  pesadas — todas compiten por el mismo threadpool] → aceptable para el
  volumen de Fase 2 (vault de un equipo, no ingesta masiva); es
  exactamente el problema que Fase 4 resuelve con Celery+Redis.
- [Cambiar `/upload` de síncrono a `202` es un cambio de contrato
  **BREAKING**] → no hay consumidores externos del API todavía (solo el
  propio frontend, que se actualiza en el mismo change), así que el
  impacto real es nulo hoy.
- [Polling cada ~1s desde varias pestañas/usuarios genera carga
  innecesaria] → volumen bajo esperado en este contexto (documentado como
  no-goal optimizarlo); el polling se detiene en cuanto `status` es
  `done`/`error`.

## Migration Plan

Sin Alembic, el cambio de esquema (`status`, `error_message` en
`documents`) se aplica recreando la base de datos de desarrollo — el
proyecto está en fase pre-producción (versión `0.0.1`, sin datos reales
desplegados) así que basta con documentar en `tasks.md` el borrado del
SQLite local (`data/ragvault.db`) tras el cambio. No se introduce Alembic
en este change (fuera de alcance); si el histórico de `documents`
empieza a tener valor real antes de que exista, se abrirá un change
dedicado a bootstrapping de Alembic.

Despliegue: `docker compose up -d --build` (nueva imagen backend con
LibreOffice + dependencias Python nuevas). Sin rollback especial más
allá de revertir el commit y recrear la imagen anterior — no hay
migración de datos irreversible.

## Open Questions

Ninguna bloqueante. Pendiente para el futuro: si el volumen de ingesta
crece, evaluar mover el tracker de progreso a algo compartido entre
procesos (Redis) en el mismo change que introduzca Celery (Fase 4), en
vez del diccionario en memoria actual.
