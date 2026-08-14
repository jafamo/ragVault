## Context

Existe una maqueta validada (artifact HTML autocontenido) con dos
identidades visuales completas — Ledger y Terminal — cada una con su
propio sistema de tokens, tipografías cargadas por fuente y componentes
(historial, chat, fuentes citadas, zona de subida, menú de cuenta). Este
change traslada esa maqueta a la aplicación React real, sin backend de
chat todavía. Restricciones ya fijadas y no abiertas a discusión aquí:
patrones de diseño de `CLAUDE.md` (no aplican al frontend salvo Facade
implícito en `services/api.ts`), estructura de carpetas de
`rag_vault_plan.md` §4.

## Goals / Non-Goals

**Goals:**
- Las dos identidades (Ledger, Terminal) coexisten en el mismo build y son
  intercambiables sin recargar la página.
- Tema claro/oscuro funcional en ambas identidades, con la misma paleta
  validada en la maqueta (Ledger verde/cian, Terminal ámbar/cian).
- Historial de sesiones editable (renombrar/eliminar) sobre datos en
  memoria.
- Menú de cuenta con nombre de usuario, tema, modelo (lista estática) y
  cerrar sesión (stub).
- El `GET /health` real sigue mostrándose, ahora integrado en la cabecera.

**Non-Goals:**
- Ninguna llamada real a `/chat`, `/upload`, `/sessions`, `/tags` — eso es
  `rag-pipeline-basico`.
- Autenticación real — "cerrar sesión" es un stub visual.
- Persistencia de sesiones entre recargas de página.
- Listado de modelos vía API — estático en este change.

## Decisions

**1. Tokens CSS por identidad en vez de Tailwind**
`rag_vault_plan.md` §3.2 sugiere Tailwind, pero Ledger y Terminal son
identidades tipográficas y cromáticas completas (fuentes propias, texturas
de fondo, componentes con formas distintas como el "gauge" de Ledger o las
filas de proceso de Terminal). Tailwind está pensado para un único sistema
de utilidades; forzar dos identidades bespoke sobre clases utility
generaría más fricción que ahorro. Se usa CSS con custom properties
(`--tx`, `--gr`, `--brass`, etc., como en la maqueta), un fichero de tokens
por identidad (`theme/ledger.css`, `theme/terminal.css`) cargado siempre,
y un atributo `data-skin` en el nodo raíz de la app que decide qué
identidad se pinta — igual mecanismo que `data-theme` para claro/oscuro.
Alternativa descartada: Tailwind + variantes de tema vía plugin — añade
una capa de indirección sin beneficio real aquí.

**2. Zustand para estado de tema/skin, sesiones y chat**
Tal como prevé el plan. Tres stores pequeños y separados:
`useThemeStore` (skin, mode), `useSessionsStore` (sesiones de ejemplo,
activeId, renombrar, eliminar), `useChatStore` (mensajes de la sesión
activa). Separarlos evita que un cambio de tema re-renderice el chat
completo.

**3. Fuentes auto-alojadas como assets estáticos, no base64 inline**
La maqueta (artifact) embebe las fuentes en base64 porque un artifact debe
ser un único fichero autocontenido. La app real no tiene esa restricción:
las fuentes (`Fraunces`, `Public Sans`, `IBM Plex Mono`, `JetBrains Mono`,
`Work Sans`, ya descargadas para la maqueta) se copian como ficheros
`.woff2` a `frontend/src/assets/fonts/` y se referencian con `url()`
normal — Vite las sirve como asset estático. Evita inflar el bundle de CSS
con ~300 KB de base64 en cada carga.

**4. `services/api.ts` como única puerta de salida (Facade ligero)**
`health()` ya hace una llamada real. `listModels()` en este change
devuelve una lista estática (los modelos reales vistos en el Ollama del
usuario al diseñar la maqueta: `qwen2.5:14b`, `gemma2:27b`,
`deepseek-r1:14b`, `deepseek-coder-v2:16b`, `llama3.1:8b`,
`qwen2.5-coder:7b`, `deepseek-r1:7b`, `qwen2.5:7b`, `mistral:7b-instruct`)
envuelta en una función `async` que ya devuelve una `Promise`, para que
cuando exista un endpoint real (`GET /models`), solo cambie el cuerpo de
esa función y ningún componente que la consume.

**5. El input de chat es honesto sobre ser una maqueta**
Al enviar un mensaje, se añade el mensaje del usuario al hilo y se
responde con un mensaje de sistema visualmente distinto ("Vista previa —
sin pipeline RAG conectado todavía"), en vez de simular una respuesta del
LLM. Evita que alguien confunda esta UI con el producto funcional antes de
`rag-pipeline-basico`.

## Risks / Trade-offs

- [Riesgo] Mantener dos identidades visuales completas duplica el trabajo
  de estilos en cada componente nuevo futuro → Mitigación: todo componente
  se escribe contra las mismas custom properties semánticas (`--tx`,
  `--accent`, `--surface`...) definidas por ambos ficheros de tokens, así
  que en la práctica el componente no sabe qué skin está activo; solo los
  dos ficheros de tokens necesitan mantenerse en paralelo.
- [Riesgo] La lista de modelos estática quedará desactualizada si el
  usuario instala/borra modelos en Ollama → Mitigación: aceptable para este
  change (ya documentado como fuera de alcance); queda anotado en el
  proposal para no olvidarlo al planear el endpoint real.
- [Trade-off] No usar Tailwind diverge de la sugerencia original del plan
  → aceptado y documentado (decisión 1); no afecta al backend ni bloquea
  usar Tailwind en el futuro para partes de la UI que no sean bespoke.

## Migration Plan

No aplica — no hay UI previa que migrar más allá de sustituir el
`App.tsx` mínimo. Sin cambios de backend, sin estado persistente que
migrar.

## Open Questions

- Ninguna abierta; el listado de modelos estático y la ausencia de
  conexión real a chat quedan explícitamente fuera de alcance, no como
  preguntas pendientes.
