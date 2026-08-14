import { useEffect } from "react";
import { useSidebarStore } from "../../stores/sidebarStore";
import SessionList from "../Sessions/SessionList";
import TagFilter from "../Tags/TagFilter";
import UploadZone from "../Documents/UploadZone";
import AccountMenu from "./AccountMenu";

const MOBILE_QUERY = "(max-width: 768px)";

export default function Sidebar() {
  const historyCollapsed = useSidebarStore((s) => s.historyCollapsed);
  const setHistoryCollapsed = useSidebarStore((s) => s.setHistoryCollapsed);

  useEffect(() => {
    const query = window.matchMedia(MOBILE_QUERY);
    if (query.matches) setHistoryCollapsed(true);

    const listener = (e: MediaQueryListEvent) => {
      if (e.matches) setHistoryCollapsed(true);
    };
    query.addEventListener("change", listener);
    return () => query.removeEventListener("change", listener);
  }, [setHistoryCollapsed]);

  return (
    <aside className={`app-sidebar${historyCollapsed ? " app-sidebar-narrow" : ""}`}>
      <SessionList />
      <TagFilter />
      <UploadZone />
      <AccountMenu />
    </aside>
  );
}
