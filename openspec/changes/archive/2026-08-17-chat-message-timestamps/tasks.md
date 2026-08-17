## 1. Formato de fecha/hora

- [x] 1.1 Sustituir `formatTime(iso)` en `frontend/src/stores/chatStore.ts`
      por `formatDateTime(iso)`, devolviendo `dd/mm HH:mm` (locale
      `es-ES`, sin año).
- [x] 1.2 Actualizar `fromApiMessage` para usar `formatDateTime` en vez
      de `formatTime` al construir el `meta` de mensajes de usuario y
      asistente recargados.

## 2. Timestamps reales en mensajes optimistas

- [x] 2.1 En `sendMessage`, sustituir el literal `"tú · ahora"` del
      mensaje de usuario por `` `tú · ${formatDateTime(new
      Date().toISOString())}` `` (o equivalente), capturando el
      `Date.now()` de envío en una variable (`sentAt`) para el cálculo
      de duración del paso 3.
- [x] 2.2 Sustituir el literal `"ahora"` del mensaje de asistente inicial
      (antes de recibir cualquier chunk) por su fecha/hora real de
      creación, sin duración todavía (mensaje en streaming).

## 3. Duración de la respuesta

- [x] 3.1 En el handler `onDone` de `sendMessage`, calcular
      `Date.now() - sentAt` y formatear como `(ms / 1000).toFixed(1) +
      "s"`, añadiéndolo al `meta` del mensaje de asistente junto al
      modelo y la hora (p. ej. `qwen2.5:14b · 17/08 13:24 · 3.2s`).
- [x] 3.2 En `fromApiMessage`/`loadMessages`, calcular la duración de
      cada mensaje de asistente como la diferencia entre su `created_at`
      y el `created_at` del mensaje de usuario inmediatamente anterior
      en la lista ya ordenada cronológicamente que devuelve
      `GET /sessions/{id}/messages`, con el mismo formato que en 3.1.
- [x] 3.3 Verificar que un mensaje de asistente en streaming (sin `done`
      todavía) no muestra ninguna duración en su `meta`.

## 4. Verificación manual y revisión

- [x] 4.1 Probar en la app real (`/run`): enviar una pregunta y
      comprobar que el mensaje de usuario y el de asistente muestran
      fecha/hora reales desde el primer instante (sin "ahora"), que la
      duración aparece al completarse la respuesta, y que tras recargar
      la página la misma duración se mantiene.
- [x] 4.2 Ejecutar la skill `ragvault-pattern-review` sobre el diff antes
      de `git flow feature finish`.
- [x] 4.3 Añadir entrada en `CHANGELOG.md` bajo `[Sin publicar]`
      (`Added`) describiendo la fecha/hora real y la duración de
      respuesta en el chat, referenciando el change
      `chat-message-timestamps`.
