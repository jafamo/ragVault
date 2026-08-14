import SessionList from "../Sessions/SessionList";
import TagFilter from "../Tags/TagFilter";
import UploadZone from "../Documents/UploadZone";
import AccountMenu from "./AccountMenu";

export default function Sidebar() {
  return (
    <aside className="app-sidebar">
      <SessionList />
      <TagFilter />
      <UploadZone />
      <AccountMenu />
    </aside>
  );
}
