import type { Message } from "../../stores/chatStore";
import SourcesCited from "./SourcesCited";

export default function MessageBubble({ message }: { message: Message }) {
  return (
    <div className={`entry ${message.role}`}>
      <div className="entry-meta">{message.meta}</div>
      <div className="entry-body">{message.text}</div>
      {message.sources && <SourcesCited sources={message.sources} />}
    </div>
  );
}
