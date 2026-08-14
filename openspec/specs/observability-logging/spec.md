# observability-logging Specification

## Purpose
TBD - created by archiving change project-bootstrap. Update Purpose after archive.
## Requirements
### Requirement: Logging estructurado en JSON a stdout
El sistema SHALL emitir todos sus logs como objetos JSON de una línea a
stdout, usando `structlog` con `JSONRenderer`, sin escribir logs en
ficheros locales ni usar `print()` o `logging` sin estructurar en el código
de aplicación.

#### Scenario: Log de aplicación
- **WHEN** el backend emite un log de cualquier nivel durante su ejecución
- **THEN** la línea escrita en stdout es un JSON válido con, como mínimo,
  las claves `timestamp` (ISO 8601 UTC), `level`, `event`/`logger` y
  `message`

### Requirement: Correlación de logs por request
El sistema SHALL asignar un `request_id` único (UUID) a cada petición HTTP
entrante mediante un middleware, y ese `request_id` SHALL aparecer en todos
los logs emitidos durante el procesamiento de esa petición.

#### Scenario: Dos peticiones concurrentes
- **WHEN** llegan dos peticiones HTTP en paralelo
- **THEN** los logs generados por cada una llevan `request_id` distintos y
  no se mezclan entre sí

### Requirement: Nivel de log configurable
El sistema SHALL permitir configurar el nivel mínimo de log mediante la
variable de entorno `LOG_LEVEL` (a través de `Settings.log_level`), sin
requerir cambios de código para ajustarlo.

#### Scenario: Cambiar verbosidad sin redeploy de código
- **WHEN** se define `LOG_LEVEL=DEBUG` en el entorno
- **THEN** la aplicación emite logs de nivel `debug` que no aparecían con la
  configuración por defecto (`INFO`)

### Requirement: Uvicorn también loguea en JSON
El sistema SHALL sustituir la configuración de logging por defecto de
Uvicorn (texto plano) por una que emita también JSON estructurado, de forma
que no convivan dos formatos de log distintos en la misma salida.

#### Scenario: Log de acceso HTTP
- **WHEN** Uvicorn registra el acceso a una petición HTTP
- **THEN** esa línea de log también es JSON válido, con el mismo formato
  que el resto de logs de la aplicación

