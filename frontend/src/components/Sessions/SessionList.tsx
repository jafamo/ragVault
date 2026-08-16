import { useSessionsStore } from "../../stores/sessionsStore";
import { useSidebarStore } from "../../stores/sidebarStore";
import { useThemeStore } from "../../stores/themeStore";
import SessionItem from "./SessionItem";

export default function SessionList() {
  const { sessions, activeId, createSession } = useSessionsStore();
  const { historyCollapsed, toggleHistoryCollapsed } = useSidebarStore();
  const skin = useThemeStore((s) => s.skin);

  return (
    <div className={historyCollapsed ? "hist-collapsed" : undefined}>
      <div className="side-label side-label-row">
        {!historyCollapsed && (
          <span>{skin === "terminal" ? "sessions --sort=recent" : "Historial"}</span>
        )}
        <button
          type="button"
          className="hist-toggle"
          aria-label={historyCollapsed ? "Expandir historial" : "Colapsar historial"}
          aria-expanded={!historyCollapsed}
          onClick={toggleHistoryCollapsed}
        >
          {historyCollapsed ? "»" : "«"}
        </button>
      </div>
      <button
        type="button"
        className="hist-new"
        aria-label="Nuevo chat"
        title="Nuevo chat"
        onClick={createSession}
      >
        {historyCollapsed ? "+" : "+ Nuevo chat"}
      </button>
      {sessions.map((session, index) => (
        <SessionItem
          key={session.id}
          session={session}
          index={index}
          total={sessions.length}
          active={session.id === activeId}
          collapsed={historyCollapsed}
        />
      ))}
    </div>
  );
}
