## Why

En responsive, la UI tiene poco espacio para el chat: el panel HISTORIAL
ocupa ancho fijo, y la cabecera duplica controles (selector de diseño y
Claro/Oscuro) que también podrían vivir en Ajustes. Limpiar ambos libera
espacio y quita ruido visual sin perder funcionalidad.

## What Changes

- `SessionList` gana un botón de colapsar/expandir. Colapsado, se reduce
  a una tira estrecha con solo el icono/inicial de cada sesión (sin
  título ni categoría); expandido, vuelve al listado completo actual.
- El estado colapsado/expandido persiste en `localStorage` (store nuevo),
  independiente de la identidad visual.
- `TagFilter`, `UploadZone` y `AccountMenu` no cambian de comportamiento
  — siguen visibles debajo, simplificados visualmente (sin texto que
  desborde) mientras el panel está colapsado.
- Con el panel colapsado, el área de chat gana el ancho liberado.
- **Responsive**: en viewport móvil (≤768px) el panel se colapsa
  automáticamente al cargar o al cruzar ese ancho, sin esperar a que el
  usuario pulse el control — mismo mecanismo de colapso, disparado
  también por `matchMedia` además del clic manual.
- **Cabecera**: se retira el `<select>` de "Diseño" (Ledger/Terminal) y
  los botones "Claro"/"Oscuro"; queda solo un icono único (sol/luna) que
  alterna claro/oscuro.
- **Ajustes (`AccountMenu`)**: gana una fila nueva con el selector de
  diseño (Ledger/Terminal), junto a las filas ya existentes de tema y
  modelo.

## Capabilities

### Modified Capabilities

- `chat-ui-shell`:
  - "Historial de sesiones editable" se amplía para cubrir el estado
    colapsado (iconos, sin edición inline visible hasta expandir).
  - "Selector de identidad visual" se amplía: el control vive ahora en
    el menú de Ajustes, no en la cabecera.
  - "Tema claro/oscuro independiente del diseño" se amplía: la cabecera
    solo ofrece el icono único, el control con ambas opciones explícitas
    sigue en Ajustes (ya existente).
  - "Menú de cuenta con nombre de usuario" se amplía: el panel de
    Ajustes incluye también el selector de diseño.

## Impact

- **Frontend**: `frontend/src/components/Sessions/SessionList.tsx`,
  `SessionItem.tsx` (variante compacta), `stores/` (nuevo flag
  persistido), `Layout/Header.tsx` (simplificado a icono único),
  `Layout/AccountMenu.tsx` (nueva fila de diseño), estilos de
  `app-sidebar`/`side-label`/`app-titlebar`.
- Sin cambios de backend/API.
