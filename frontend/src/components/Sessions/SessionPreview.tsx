import { useEffect } from "react";
import { useChatStore } from "../../stores/chatStore";
import { useSessionsStore } from "../../stores/sessionsStore";

interface Props {
  sessionId: string;
}

export default function SessionPreview({ sessionId }: Props) {
  const loadMessages = useChatStore((s) => s.loadMessages);
  const loaded = useChatStore((s) => s.loadedSessions[sessionId]);
  const messages = useChatStore((s) => s.messagesBySession[sessionId]);
  const setActive = useSessionsStore((s) => s.setActive);

  useEffect(() => {
    loadMessages(sessionId);
  }, [sessionId, loadMessages]);

  const isLoading = loaded && messages === undefined;

  return (
    <div className="hist-preview" onClick={(e) => e.stopPropagation()}>
      {isLoading && <div className="hist-preview-loading">Cargando mensajes…</div>}
      {!isLoading && messages?.length === 0 && (
        <div className="hist-preview-empty">Sin mensajes todavía.</div>
      )}
      {!isLoading && messages && messages.length > 0 && (
        <div className="hist-preview-messages">
          {messages.map((m) => (
            <div key={m.id} className={`hist-preview-msg hist-preview-msg-${m.role}`}>
              <span className="hist-preview-role">{m.role === "user" ? "tú" : "IA"}</span>
              <span className="hist-preview-text">{m.text}</span>
            </div>
          ))}
        </div>
      )}
      <button
        type="button"
        className="hist-preview-open"
        onClick={() => setActive(sessionId)}
      >
        Abrir en el chat
      </button>
    </div>
  );
}
