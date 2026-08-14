# document-ingestion Specification

## Purpose
TBD - created by archiving change rag-pipeline-basico. Update Purpose after archive.
## Requirements
### Requirement: Selección de loader por extensión (Strategy + Factory)
El sistema SHALL seleccionar la estrategia de carga de un documento según
su extensión mediante un `LoaderFactory`, soportando `.pdf` en este
change y devolviendo un error controlado para cualquier otra extensión,
sin que ninguna ruta de API instancie loaders directamente.

#### Scenario: Extensión soportada
- **WHEN** se sube un fichero `.pdf`
- **THEN** `LoaderFactory` selecciona el loader de PDF y procede con la
  ingesta

#### Scenario: Extensión no soportada
- **WHEN** se sube un fichero con extensión distinta de `.pdf` (p. ej.
  `.docx`)
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
El sistema SHALL exponer `POST /upload` que reciba un fichero, ejecute la
ingesta completa (carga → chunking → embeddings → almacenamiento) y
devuelva la metadata del documento resultante o un error controlado.

#### Scenario: Subida exitosa
- **WHEN** se hace `POST /upload` con un PDF válido
- **THEN** la respuesta incluye el id del documento, su nombre y el
  número de chunks indexados

### Requirement: Zona de subida funcional en la UI
El sistema SHALL permitir subir un documento desde `UploadZone` tanto por
selección de fichero (clic) como por arrastrar-y-soltar, mostrando el
resultado real de `POST /upload` (éxito con nº de chunks, o error).

#### Scenario: Subida desde la UI
- **WHEN** el usuario arrastra un PDF sobre la zona de subida o lo
  selecciona con el explorador de ficheros
- **THEN** se envía a `POST /upload` y, al completarse, la UI muestra el
  nombre del documento y su número de chunks indexados

