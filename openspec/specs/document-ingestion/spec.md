# document-ingestion Specification

## Purpose
TBD - created by archiving change rag-pipeline-basico. Update Purpose after archive.
## Requirements
### Requirement: Selección de loader por extensión (Strategy + Factory)
El sistema SHALL seleccionar la estrategia de carga de un documento según
su extensión mediante un `LoaderFactory`, soportando `.pdf`, `.docx`,
`.odt`, `.xlsx`, `.ods`, `.csv`, `.md`, `.txt`, `.pptx` y `.ppt`, y
devolviendo un error controlado para cualquier otra extensión, sin que
ninguna ruta de API instancie loaders directamente.

#### Scenario: Extensión soportada
- **WHEN** se sube un fichero con una de las extensiones soportadas
  (`.pdf`, `.docx`, `.odt`, `.xlsx`, `.ods`, `.csv`, `.md`, `.txt`,
  `.pptx`, `.ppt`)
- **THEN** `LoaderFactory` selecciona el loader correspondiente y procede
  con la ingesta

#### Scenario: Extensión no soportada
- **WHEN** se sube un fichero con una extensión distinta de las
  soportadas (p. ej. `.rtf`)
- **THEN** el sistema responde con un error controlado (415) indicando
  qué formatos soporta, sin lanzar una excepción no controlada

### Requirement: Chunking configurable
El sistema SHALL dividir el texto extraído en chunks usando
`RecursiveCharacterTextSplitter` con tamaño y solapamiento configurables
vía `Settings` (por defecto 1000/200 tokens, según `rag_vault_plan.md`
§7.1).

#### Scenario: Documento largo se trocea
- **WHEN** se ingiere un PDF cuyo texto supera el tamaño de un chunk
- **THEN** el documento queda dividido en múltiples chunks con
  solapamiento entre consecutivos

### Requirement: Indexación en el vector store
El sistema SHALL generar embeddings de cada chunk con el modelo Ollama
configurado (`Settings.ollama_embed_model`) y almacenarlos en ChromaDB a
través de un `VectorStoreRepository`, con metadata suficiente para
recuperar el documento y la página de origen en una consulta posterior.

#### Scenario: Chunks disponibles para retrieval
- **WHEN** termina la ingesta de un documento
- **THEN** sus chunks son recuperables por similitud semántica desde
  `VectorStoreRepository.similarity_search`

### Requirement: Metadata de documento persistida
El sistema SHALL registrar cada documento subido en una tabla `documents`
(SQLite, vía `DocumentRepository`) con al menos: id, nombre de fichero,
formato, fecha de subida y número de chunks generados.

#### Scenario: Consultar documentos ingeridos
- **WHEN** se sube un documento correctamente
- **THEN** `DocumentRepository.list()` incluye una entrada con su nombre,
  formato y `chunk_count`

### Requirement: Endpoint de subida
El sistema SHALL exponer `POST /upload` que reciba un fichero, lo
persista y cree su registro de documento con `status="queued"`,
devolviendo `202 Accepted` con la metadata inicial del documento sin
esperar a que termine el resto del pipeline (carga → chunking →
embeddings → almacenamiento), que se ejecuta en segundo plano.

#### Scenario: Subida aceptada
- **WHEN** se hace `POST /upload` con un fichero de un formato soportado
- **THEN** la respuesta es `202` e incluye el id del documento, su nombre
  y `status: "queued"`, y el pipeline de ingesta arranca en segundo plano
  sin bloquear la petición

### Requirement: Zona de subida funcional en la UI
El sistema SHALL permitir subir un documento desde `UploadZone` tanto por
selección de fichero (clic) como por arrastrar-y-soltar, restringiendo la
selección a las extensiones soportadas (`.pdf`, `.docx`, `.odt`, `.xlsx`,
`.ods`, `.csv`, `.md`, `.txt`, `.pptx`, `.ppt`), mostrando el progreso de
subida y de parseo por separado, y el resultado final (éxito con nº de
chunks, o error).

#### Scenario: Subida desde la UI
- **WHEN** el usuario arrastra un documento de un formato soportado sobre
  la zona de subida o lo selecciona con el explorador de ficheros
- **THEN** se envía a `POST /upload` y, al completar la ingesta en
  segundo plano, la UI muestra el nombre del documento y su número de
  chunks indexados

#### Scenario: Selector de fichero limitado a formatos soportados
- **WHEN** el usuario abre el explorador de ficheros desde `UploadZone`
- **THEN** el diálogo del sistema operativo filtra por defecto a las
  extensiones soportadas por el backend

### Requirement: Manejo de errores específico por formato
El sistema SHALL distinguir, en cada loader, los errores propios del
parseo de su formato (fichero corrupto, protegido con contraseña, vacío,
o versión no soportada por la librería subyacente) de errores internos
no previstos, y traducirlos a un estado de ingesta `error` con un mensaje
que identifique el formato y la causa, sin exponer detalles internos
(tracebacks) al usuario.

#### Scenario: Fichero corrupto o vacío
- **WHEN** se sube un fichero con una extensión soportada pero cuyo
  contenido está corrupto, vacío, o protegido con contraseña
- **THEN** el documento queda con `status="error"` y un
  `error_message` legible que identifica el formato y la causa,
  visible en `GET /documents/{id}/status`, sin tumbar el proceso

### Requirement: Reintentos configurables ante fallo de embeddings
El sistema SHALL reintentar automáticamente la llamada de embeddings
contra Ollama hasta `Settings.ingestion_max_retries` veces (configurable
vía `INGESTION_MAX_RETRIES`, default `3`) ante un fallo transitorio,
antes de marcar el documento como `status="error"`. Los errores de
parseo (`LoaderParsingError`) no se reintentan.

#### Scenario: Fallo transitorio de embeddings se recupera
- **WHEN** la llamada de embeddings a Ollama falla por un error
  transitorio (timeout, conexión) durante la ingesta de un documento
- **THEN** el sistema reintenta hasta `INGESTION_MAX_RETRIES` veces con
  backoff antes de continuar o de marcar el documento como `error`

#### Scenario: Se agotan los reintentos
- **WHEN** el fallo de embeddings persiste tras agotar
  `INGESTION_MAX_RETRIES` intentos
- **THEN** el documento queda con `status="error"` y `error_message`
  describe el último fallo, visible en `GET /documents/{id}/status`

### Requirement: Progreso de ingesta observable
El sistema SHALL notificar el progreso de la ingesta de un documento
(subida y, por separado, cada etapa del parseo: carga, chunking,
embeddings, indexado) mediante un `IngestionProgressTracker` (Observer)
consultable vía `GET /documents/{id}/status`, permitiendo que el
frontend muestre progreso de subida y de parseo como señales
independientes y no bloqueantes.

#### Scenario: Consultar progreso durante el parseo
- **WHEN** un documento está en `status="processing"` tras un
  `POST /upload` aceptado
- **THEN** `GET /documents/{id}/status` devuelve la etapa actual
  (`stage`) y un porcentaje aproximado (`percent`) que avanza según el
  pipeline procesa el documento

#### Scenario: Barra de subida independiente de la de parseo
- **WHEN** el usuario sube un fichero desde `UploadZone`
- **THEN** la UI muestra una barra de progreso de subida (bytes
  transferidos) mientras dura la petición `POST /upload`, y al recibir
  el `202` muestra una segunda barra de progreso de parseo que se
  actualiza sondeando `GET /documents/{id}/status` sin bloquear el resto
  de la interfaz

#### Scenario: Ingesta completada
- **WHEN** el pipeline en segundo plano termina de indexar el documento
- **THEN** `GET /documents/{id}/status` devuelve `status="done"` y la UI
  deja de sondear y muestra el resultado final (nombre y nº de chunks)
