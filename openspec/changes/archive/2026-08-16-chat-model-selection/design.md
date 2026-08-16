## Context

`AccountMenu.tsx` mantiene el modelo elegido como `useState` local, nunca
propagado. `services/api.ts:listModels()` devuelve `MOCK_MODELS`, una
constante en `data/mockModels.ts` que además ya coincide, por casualidad,
con los modelos reales que el usuario tiene instalados hoy en su Ollama —
pero es una coincidencia frágil: en cuanto instale o quite un modelo,
quedará desincronizada. `core/llm_provider.get_llm()` construye siempre
`ChatOllama(model=settings.ollama_model)`, y `POST /chat`
(`api/routes/chat.py`) no acepta ningún override.

## Goals / Non-Goals

**Goals:**
- El modelo mostrado en el selector siempre refleja los modelos realmente
  disponibles en el Ollama configurado.
- Elegir un modelo distinto tiene efecto real en la siguiente respuesta
  del chat.

**Non-Goals:**
- Persistir la preferencia de modelo entre recargas de página o entre
  sesiones (decidido: solo en memoria de la pestaña).
- Permitir parámetros de generación adicionales (temperatura, etc.) — fuera
  de alcance, solo se cubre la elección de modelo.
- Validar que el modelo elegido cabe en la RAM disponible — Ollama ya
  devuelve su propio error si el modelo no existe o falla al cargar, y ese
  error se propaga tal cual (mensaje explícito, sin inventar respuesta),
  igual que cualquier otro fallo de Ollama hoy.

## Decisions

- **`GET /models` llama a Ollama directamente (`{OLLAMA_BASE_URL}/api/tags`)
  con `httpx`, igual que `GET /health`** — no se cachea la lista en SQL ni
  en memoria del proceso; es una consulta de solo lectura y de bajo
  volumen (se llama una vez al abrir el menú de cuenta), así que
  cachearla sería complejidad innecesaria.
- **Se excluye el modelo de embeddings de la lista** comparando por nombre
  exacto contra `settings.ollama_embed_model`, no por heurística de nombre
  (p. ej. buscar "embed" en el string) — evita falsos negativos si algún
  modelo de generación instalado contuviera esa palabra.
- **`ChatRequest.model` es opcional (`str | None = None`)**: si no se
  manda, se preserva el comportamiento actual (`settings.ollama_model`).
  Evita romper compatibilidad con cualquier otro consumidor de `POST
  /chat` que no mande el campo.
- **`ChatResponse` gana un campo `model`** con el modelo que realmente
  generó la respuesta, para que la UI pueda mostrarlo en el meta del
  mensaje (ya hay un formato "modelo · hora" en los mensajes mock
  existentes) — confirma al usuario que el cambio de modelo tuvo efecto.
- **Store de Zustand nuevo (`modelStore`) en vez de extender
  `themeStore`**: el modelo activo no es una preferencia visual como
  skin/tema, y su valor por defecto depende de una respuesta de red
  (`GET /models`), no de un valor fijo — mantenerlo separado evita
  acoplar la inicialización de un store sin red (`themeStore`) a una
  llamada asíncrona.
- **Sin persistencia en `localStorage`** (decidido): al recargar la
  página, el selector vuelve a mostrar el modelo por defecto que reporte
  el backend (`OLLAMA_MODEL`).

## Risks / Trade-offs

- [Si Ollama no responde, `GET /models` fallaría y el selector se
  quedaría sin opciones] → se trata igual que el fallo ya manejado en
  `GET /health`: la UI puede mostrar el modelo por defecto de
  `Settings` como única opción y no bloquear el resto del menú.
- [Un usuario podría seleccionar un modelo que deja de estar disponible
  entre que se cargó la lista y se envía el mensaje] → el error de Ollama
  se propaga como el mensaje de error explícito ya definido en el
  requirement "Chat honesto sobre ser una maqueta" — no requiere manejo
  especial adicional.

## Migration Plan

Cambio aditivo y de comportamiento en un endpoint existente
(`POST /chat` sigue funcionando igual sin el campo `model`) más un
endpoint nuevo (`GET /models`) — sin migración de datos. Deploy backend
antes que frontend para que `GET /models` exista cuando el frontend lo
llame.

## Open Questions

Ninguna bloqueante.
