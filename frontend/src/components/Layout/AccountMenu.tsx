import { useEffect, useState } from "react";
import { useThemeStore } from "../../stores/themeStore";
import { listModels } from "../../services/api";
import { DEFAULT_MODEL } from "../../data/mockModels";

const USER_NAME = "Javier";

export default function AccountMenu() {
  const { skin, mode, setSkin, setMode } = useThemeStore();
  const [models, setModels] = useState<readonly string[]>([DEFAULT_MODEL]);
  const [model, setModel] = useState<string>(DEFAULT_MODEL);
  const [loggedOut, setLoggedOut] = useState(false);

  useEffect(() => {
    listModels().then(setModels);
  }, []);

  function handleLogout() {
    setLoggedOut(true);
    setTimeout(() => setLoggedOut(false), 1800);
  }

  const isTerminal = skin === "terminal";

  return (
    <details className="settings">
      <summary className="settings-summary">
        {isTerminal ? (
          <span className="user-chip">
            <span className="proc-dot" style={{ marginTop: 0 }} />
            <span className="user-name">javier@ragvault</span>
          </span>
        ) : (
          <span className="user-chip">
            <span className="avatar">{USER_NAME[0]}</span>
            <span className="user-name">{USER_NAME}</span>
          </span>
        )}
      </summary>
      <div className="settings-panel">
        <div className="settings-row">
          <span className="settings-label">{isTerminal ? "skin" : "Diseño"}</span>
          <div className="settings-seg" role="group" aria-label="Diseño">
            <button
              type="button"
              aria-pressed={skin === "ledger"}
              onClick={() => setSkin("ledger")}
            >
              Ledger
            </button>
            <button
              type="button"
              aria-pressed={skin === "terminal"}
              onClick={() => setSkin("terminal")}
            >
              Terminal
            </button>
          </div>
        </div>

        <div className="settings-row">
          <span className="settings-label">{isTerminal ? "theme" : "Tema"}</span>
          <div className="settings-seg" role="group" aria-label="Tema de color">
            <button
              type="button"
              aria-pressed={mode === "light"}
              onClick={() => setMode("light")}
            >
              {isTerminal ? "light" : "Claro"}
            </button>
            <button
              type="button"
              aria-pressed={mode === "dark"}
              onClick={() => setMode("dark")}
            >
              {isTerminal ? "dark" : "Oscuro"}
            </button>
          </div>
        </div>

        <label className="settings-row">
          <span className="settings-label">{isTerminal ? "model --ollama" : "Modelo (Ollama)"}</span>
          <select
            className="settings-select"
            value={model}
            onChange={(e) => setModel(e.target.value)}
          >
            {models.map((m) => (
              <option key={m} value={m}>
                {m}
              </option>
            ))}
          </select>
        </label>

        <button
          type="button"
          className="settings-logout"
          disabled={loggedOut}
          onClick={handleLogout}
        >
          {loggedOut
            ? isTerminal
              ? "logged out"
              : "Sesión cerrada"
            : isTerminal
              ? "$ logout"
              : "Cerrar sesión"}
        </button>
      </div>
    </details>
  );
}
