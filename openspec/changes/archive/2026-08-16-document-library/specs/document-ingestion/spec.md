## MODIFIED Requirements

### Requirement: Metadata de documento persistida
El sistema SHALL registrar cada documento subido en una tabla `documents`
(SQLite, vía `DocumentRepository`) con al menos: id, nombre de fichero,
formato, fecha de subida, número de chunks generados, tamaño en bytes
(`size_bytes`) y ruta absoluta del fichero en disco (`absolute_path`).

#### Scenario: Consultar documentos ingeridos
- **WHEN** se sube un documento correctamente
- **THEN** `DocumentRepository.list()` incluye una entrada con su nombre,
  formato, `chunk_count`, `size_bytes` y `absolute_path`

## ADDED Requirements

### Requirement: Cancelación de ingesta en curso
El sistema SHALL permitir señalar la cancelación de la ingesta de un
documento mientras está `status="processing"`, comprobando dicha señal en
puntos de control entre etapas (tras la carga, tras el chunking, y entre
lotes de embeddings), y marcando el documento como `status="cancelled"`
—sin escribir más chunks y sin tratarlo como `status="error"`— en cuanto
la detecta.

#### Scenario: Cancelación reconocida entre etapas
- **WHEN** se solicita la cancelación de un documento cuya ingesta está en
  la etapa de embeddings
- **THEN** el pipeline detiene el procesamiento en el siguiente punto de
  control, deja de añadir chunks nuevos al vector store y marca el
  documento con `status="cancelled"`

#### Scenario: Sin señal de cancelación, la ingesta continúa normalmente
- **WHEN** un documento se está procesando y no se solicita su cancelación
- **THEN** el pipeline completa todas las etapas y marca el documento como
  `status="done"` igual que hoy
