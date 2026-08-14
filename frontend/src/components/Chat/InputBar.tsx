import { useState, type FormEvent } from "react";
import { useSessionsStore } from "../../stores/sessionsStore";
import { useChatStore } from "../../stores/chatStore";
import { useThemeStore } from "../../stores/themeStore";

export default function InputBar() {
  const [text, setText] = useState("");
  const activeId = useSessionsStore((s) => s.activeId);
  const sendMessage = useChatStore((s) => s.sendMessage);
  const skin = useThemeStore((s) => s.skin);

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!activeId) return;
    sendMessage(activeId, text);
    setText("");
  }

  return (
    <form className="input-bar" onSubmit={handleSubmit}>
      <input
        type="text"
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder={
          skin === "terminal" ? "> escribe una pregunta…" : "Escribe una pregunta…"
        }
        aria-label="Mensaje"
      />
      <button type="submit">{skin === "terminal" ? "$ send" : "Enviar"}</button>
    </form>
  );
}
