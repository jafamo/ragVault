import { useState, type FormEvent } from "react";
import { useSessionsStore } from "../../stores/sessionsStore";
import { useChatStore } from "../../stores/chatStore";
import { useThemeStore } from "../../stores/themeStore";

export default function InputBar() {
  const [text, setText] = useState("");
  const activeId = useSessionsStore((s) => s.activeId);
  const sendMessage = useChatStore((s) => s.sendMessage);
  const pendingSessionId = useChatStore((s) => s.pendingSessionId);
  const skin = useThemeStore((s) => s.skin);

  const isPending = pendingSessionId !== null && pendingSessionId === activeId;

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!activeId || isPending || !text.trim()) return;
    sendMessage(activeId, text);
    setText("");
  }

  const sendLabel = isPending
    ? skin === "terminal"
      ? "$ waiting…"
      : "Esperando…"
    : skin === "terminal"
      ? "$ send"
      : "Enviar";

  return (
    <form className="input-bar" onSubmit={handleSubmit}>
      <input
        type="text"
        value={text}
        onChange={(e) => setText(e.target.value)}
        disabled={isPending}
        placeholder={
          skin === "terminal" ? "> escribe una pregunta…" : "Escribe una pregunta…"
        }
        aria-label="Mensaje"
      />
      <button type="submit" disabled={isPending}>
        {sendLabel}
      </button>
    </form>
  );
}
