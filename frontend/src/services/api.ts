import { MOCK_MODELS } from "../data/mockModels";

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export interface HealthResponse {
  status: string;
  ollama: "reachable" | "unreachable";
}

export async function health(): Promise<HealthResponse> {
  const res = await fetch(`${API_URL}/health`);
  return res.json();
}

// Lista estática — no existe todavía GET /models en el backend.
// Ver openspec/changes/chat-ui-shell/design.md, decisión 4.
export async function listModels(): Promise<readonly string[]> {
  return MOCK_MODELS;
}
