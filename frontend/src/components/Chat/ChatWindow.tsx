import { useEffect, useRef } from "react";
import { useSessionsStore } from "../../stores/sessionsStore";
import { useChatStore } from "../../stores/chatStore";
import MessageBubble from "./MessageBubble";
import InputBar from "./InputBar";

export default function ChatWindow() {
  const activeId = useSessionsStore((s) => s.activeId);
  const messages = useChatStore((s) => s.messagesBySession[activeId] ?? []);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ block: "end" });
  }, [messages.length]);

  return (
    <div style={{ display: "flex", flexDirection: "column", minHeight: 0, height: "100%" }}>
      <main className="app-main" style={{ flex: 1 }}>
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}
        <div ref={bottomRef} />
      </main>
      <InputBar />
    </div>
  );
}
