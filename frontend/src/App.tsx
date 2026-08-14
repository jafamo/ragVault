import { useEffect } from "react";
import { useThemeStore } from "./stores/themeStore";
import Header from "./components/Layout/Header";
import Sidebar from "./components/Layout/Sidebar";
import ChatWindow from "./components/Chat/ChatWindow";

export default function App() {
  const { skin, mode } = useThemeStore();

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
        <ChatWindow />
      </div>
    </div>
  );
}
