import { useEffect, useState } from "react";
import { health } from "../../services/api";
import { useThemeStore, type Skin } from "../../stores/themeStore";
import { DEFAULT_MODEL } from "../../data/mockModels";

const SKIN_LABELS: Record<Skin, string> = {
  ledger: "Ledger — bóveda",
  terminal: "Terminal — runtime local",
};

export default function Header() {
  const { skin, mode, setSkin, setMode } = useThemeStore();
  const [ollamaStatus, setOllamaStatus] = useState<"reachable" | "unreachable" | "checking">(
    "checking"
  );

  useEffect(() => {
    health()
      .then((res) => setOllamaStatus(res.ollama))
      .catch(() => setOllamaStatus("unreachable"));
  }, []);

  const brand = skin === "terminal" ? "ragvault" : "RagVault";

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
        <span>{DEFAULT_MODEL}</span>

        <select
          aria-label="Diseño"
          value={skin}
          onChange={(e) => setSkin(e.target.value as Skin)}
        >
          <option value="ledger">{SKIN_LABELS.ledger}</option>
          <option value="terminal">{SKIN_LABELS.terminal}</option>
        </select>

        <span role="group" aria-label="Tema de color">
          <button
            type="button"
            aria-pressed={mode === "light"}
            onClick={() => setMode("light")}
          >
            Claro
          </button>
          <button
            type="button"
            aria-pressed={mode === "dark"}
            onClick={() => setMode("dark")}
          >
            Oscuro
          </button>
        </span>
      </div>
    </header>
  );
}
