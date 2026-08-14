import { useEffect, useState } from "react";

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

type HealthResponse = {
  status: string;
  ollama: "reachable" | "unreachable";
};

export default function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${API_URL}/health`)
      .then((res) => res.json())
      .then(setHealth)
      .catch(() => setError("No se pudo contactar con el backend"));
  }, []);

  return (
    <main>
      <h1>RagVault</h1>
      {error && <p>{error}</p>}
      {health && (
        <p>
          Backend: {health.status} — Ollama: {health.ollama}
        </p>
      )}
    </main>
  );
}
