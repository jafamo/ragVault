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

export interface DocumentResponse {
  id: string;
  filename: string;
  format: string;
  chunk_count: number;
  uploaded_at: string;
}

export async function uploadDocument(file: File): Promise<DocumentResponse> {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${API_URL}/upload`, { method: "POST", body: formData });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail ?? `Error ${res.status} al subir el documento`);
  }
  return res.json();
}

export interface SourceResponse {
  document_id: string;
  document_name: string;
  page: number | null;
  chunk_text: string;
  similarity_score: number;
}

export interface ChatApiResponse {
  answer: string;
  sources: SourceResponse[];
}

export async function sendChatMessage(message: string): Promise<ChatApiResponse> {
  const res = await fetch(`${API_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });
  if (!res.ok) {
    throw new Error(`Error ${res.status} al consultar el backend`);
  }
  return res.json();
}
