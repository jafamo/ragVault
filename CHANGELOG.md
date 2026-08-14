# Changelog

Todos los cambios notables de este proyecto se documentan en este fichero.

El formato se basa en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/),
y este proyecto usa [Semantic Versioning](https://semver.org/lang/es/)
(`MAJOR.MINOR.PATCH`).

## [Sin publicar]

### Added

### Changed

### Fixed

### Removed

## [0.0.1] - 2026-08-14

### Fixed

- Corregido el patrón `data/` en `.gitignore`, que excluía sin querer
  `frontend/src/data/` (incluyendo `mockModels.ts`) al no estar anclado a
  la raíz del repo. Esto rompía el build de producción con Vite
  (`Failed to resolve import "../../data/mockModels"`).
