import { useSessionsStore } from "../../stores/sessionsStore";
import { useThemeStore } from "../../stores/themeStore";
import SessionItem from "./SessionItem";

export default function SessionList() {
  const { sessions, activeId } = useSessionsStore();
  const skin = useThemeStore((s) => s.skin);

  return (
    <div>
      <div className="side-label">
        {skin === "terminal" ? "sessions --sort=recent" : "Historial"}
      </div>
      {sessions.map((session, index) => (
        <SessionItem
          key={session.id}
          session={session}
          index={index}
          total={sessions.length}
          active={session.id === activeId}
        />
      ))}
    </div>
  );
}
