import { Suspense, lazy, useEffect } from "react";
import { useThemeStore } from "./stores/themeStore";
import { useViewStore } from "./stores/viewStore";
import Header from "./components/Layout/Header";
import Sidebar from "./components/Layout/Sidebar";
import ChatWindow from "./components/Chat/ChatWindow";

const StatsDashboard = lazy(() => import("./components/Stats/StatsDashboard"));

export default function App() {
  const { skin, mode } = useThemeStore();
  const { view } = useViewStore();

  useEffect(() => {
    if (mode) {
      document.documentElement.setAttribute("data-theme", mode);
    } else {
      document.documentElement.removeAttribute("data-theme");
    }
  }, [mode]);

  return (
    <div className="app-shell" data-skin={skin}>
      <Header />
      <div className="app-body">
        <Sidebar />
        {view === "stats" ? (
          <Suspense fallback={<div className="stats-loading">Cargando estadísticas…</div>}>
            <StatsDashboard />
          </Suspense>
        ) : (
          <ChatWindow />
        )}
      </div>
    </div>
  );
}
