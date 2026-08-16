import { useRef } from "react";
import { useSessionsStore, type Session } from "../../stores/sessionsStore";
import { useThemeStore } from "../../stores/themeStore";
import SessionPreview from "./SessionPreview";

interface Props {
  session: Session;
  index: number;
  total: number;
  active: boolean;
  collapsed?: boolean;
  previewExpanded?: boolean;
  onTogglePreview?: () => void;
}

function formatRelativeTime(iso: string): string {
  const diffDays = Math.floor((Date.now() - new Date(iso).getTime()) / (1000 * 60 * 60 * 24));
  if (diffDays <= 0) return "hoy";
  if (diffDays === 1) return "ayer";
  return `${diffDays} días`;
}

export default function SessionItem({
  session,
  index,
  total,
  active,
  collapsed = false,
  previewExpanded = false,
  onTogglePreview,
}: Props) {
  const { setActive, renameSession, deleteSession } = useSessionsStore();
  const skin = useThemeStore((s) => s.skin);
  const titleRef = useRef<HTMLSpanElement>(null);
  const time = formatRelativeTime(session.updatedAt);

  const rowClass = skin === "terminal" ? "proc-row" : "ledger-row";

  function commitTitle() {
    const text = titleRef.current?.textContent ?? "";
    renameSession(session.id, text);
  }

  if (collapsed) {
    return (
      <button
        type="button"
        className={`hist-row-collapsed${active ? " active" : ""}`}
        title={session.title}
        aria-label={session.title}
        onClick={() => setActive(session.id)}
      >
        {session.title.trim().charAt(0).toUpperCase() || "?"}
      </button>
    );
  }

  const previewToggle = (
    <button
      type="button"
      className="hist-preview-toggle"
      aria-label={previewExpanded ? "Colapsar vista previa" : "Previsualizar mensajes"}
      aria-expanded={previewExpanded}
      onClick={(e) => {
        e.stopPropagation();
        onTogglePreview?.();
      }}
    >
      {previewExpanded ? "▾" : "▸"}
    </button>
  );

  if (skin === "terminal") {
    return (
      <>
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
          <span className="proc-time">{time}</span>
          {previewToggle}
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
        {previewExpanded && <SessionPreview sessionId={session.id} />}
      </>
    );
  }

  return (
    <>
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
        </span>
        <span className="ltime">{time}</span>
        {previewToggle}
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
      {previewExpanded && <SessionPreview sessionId={session.id} />}
    </>
  );
}
