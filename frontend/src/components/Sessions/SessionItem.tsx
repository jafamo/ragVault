import { useRef } from "react";
import { useSessionsStore, type Session } from "../../stores/sessionsStore";
import { useThemeStore } from "../../stores/themeStore";

interface Props {
  session: Session;
  index: number;
  total: number;
  active: boolean;
}

export default function SessionItem({ session, index, total, active }: Props) {
  const { setActive, renameSession, deleteSession } = useSessionsStore();
  const skin = useThemeStore((s) => s.skin);
  const titleRef = useRef<HTMLSpanElement>(null);

  const rowClass = skin === "terminal" ? "proc-row" : "ledger-row";

  function commitTitle() {
    const text = titleRef.current?.textContent ?? "";
    renameSession(session.id, text);
  }

  if (skin === "terminal") {
    return (
      <div
        className={`${rowClass} hist-row${active ? " active" : ""}`}
        onClick={() => setActive(session.id)}
      >
        <span className="proc-dot" />
        <span className="proc-id">#{String(38 + total - index).padStart(3, "0")}</span>
        <span
          ref={titleRef}
          className="proc-title hist-title"
          contentEditable
          suppressContentEditableWarning
          spellCheck={false}
          onClick={(e) => e.stopPropagation()}
          onBlur={commitTitle}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              e.preventDefault();
              (e.target as HTMLElement).blur();
            }
          }}
        >
          {session.title}
        </span>
        <span className="proc-time">{session.time}</span>
        <button
          type="button"
          className="hist-del"
          aria-label="Eliminar sesión"
          onClick={(e) => {
            e.stopPropagation();
            deleteSession(session.id);
          }}
        >
          ×
        </button>
      </div>
    );
  }

  return (
    <div
      className={`${rowClass} hist-row${active ? " active" : ""}`}
      onClick={() => setActive(session.id)}
    >
      <span className="lnum">{String(total - index).padStart(3, "0")}</span>
      <span>
        <span
          ref={titleRef}
          className="ltitle hist-title"
          contentEditable
          suppressContentEditableWarning
          spellCheck={false}
          onClick={(e) => e.stopPropagation()}
          onBlur={commitTitle}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              e.preventDefault();
              (e.target as HTMLElement).blur();
            }
          }}
        >
          {session.title}
        </span>
        <span className="ltag">{session.tag}</span>
      </span>
      <span className="ltime">{session.time}</span>
      <button
        type="button"
        className="hist-del"
        aria-label="Eliminar sesión"
        onClick={(e) => {
          e.stopPropagation();
          deleteSession(session.id);
        }}
      >
        ×
      </button>
    </div>
  );
}
