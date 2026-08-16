import { useEffect, useState } from "react";
import { health } from "../../services/api";
import { useThemeStore } from "../../stores/themeStore";
import { useModelStore } from "../../stores/modelStore";

export default function Header() {
  const { skin, mode, setMode } = useThemeStore();
  const model = useModelStore((s) => s.model);
  const [ollamaStatus, setOllamaStatus] = useState<"reachable" | "unreachable" | "checking">(
    "checking"
  );
  const [systemPrefersDark, setSystemPrefersDark] = useState(
    () => window.matchMedia?.("(prefers-color-scheme: dark)").matches ?? false,
  );

  useEffect(() => {
    health()
      .then((res) => setOllamaStatus(res.ollama))
      .catch(() => setOllamaStatus("unreachable"));
  }, []);

  useEffect(() => {
    const query = window.matchMedia("(prefers-color-scheme: dark)");
    const listener = (e: MediaQueryListEvent) => setSystemPrefersDark(e.matches);
    query.addEventListener("change", listener);
    return () => query.removeEventListener("change", listener);
  }, []);

  const brand = skin === "terminal" ? "ragvault" : "RagVault";
  const isDark = mode === "dark" || (mode === null && systemPrefersDark);

  return (
    <header className="app-titlebar">
      <div className="brand">
        {skin === "ledger" && <span className="dial" />}
        <span className="brand-name">{brand}</span>
      </div>

      <div className="status">
        <span>
          <span className={`dot${ollamaStatus === "unreachable" ? " is-down" : ""}`} />
          {ollamaStatus === "checking"
            ? "Comprobando Ollama…"
            : ollamaStatus === "reachable"
              ? "Ollama conectado"
              : "Ollama no disponible"}
        </span>
        <span>{model}</span>

        <button
          type="button"
          className="theme-toggle"
          aria-label={isDark ? "Cambiar a tema claro" : "Cambiar a tema oscuro"}
          onClick={() => setMode(isDark ? "light" : "dark")}
        >
          {isDark ? "☀" : "☾"}
        </button>
      </div>
    </header>
  );
}
