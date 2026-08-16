import { DEFAULT_MODEL } from "../data/mockModels";

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export interface HealthResponse {
  status: string;
  ollama: "reachable" | "unreachable";
}

export async function health(): Promise<HealthResponse> {
  const res = await fetch(`${API_URL}/health`);
  return res.json();
}

export interface ModelsResponse {
  models: string[];
  default: string;
}

export async function listModels(): Promise<ModelsResponse> {
  const res = await fetch(`${API_URL}/models`);
  if (!res.ok) {
    return { models: [DEFAULT_MODEL], default: DEFAULT_MODEL };
  }
  return res.json();
}

export interface DocumentResponse {
  id: string;
  filename: string;
  format: string;
  chunk_count: number;
  uploaded_at: string;
  status: string;
}

export interface DocumentStatusResponse {
  status: string;
  stage: string | null;
  percent: number | null;
  error_message: string | null;
  chunk_count: number;
}

export function uploadDocument(
  file: File,
  onUploadProgress?: (percent: number) => void,
): Promise<DocumentResponse> {
  const formData = new FormData();
  formData.append("file", file);

  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", `${API_URL}/upload`);

    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable && onUploadProgress) {
        onUploadProgress(Math.round((event.loaded / event.total) * 100));
      }
    };

    xhr.onload = () => {
      let body: unknown = {};
      try {
        body = JSON.parse(xhr.responseText);
      } catch {
        // respuesta no-JSON, se maneja como error genérico abajo
      }
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(body as DocumentResponse);
      } else {
        const detail = (body as { detail?: string }).detail;
        reject(new Error(detail ?? `Error ${xhr.status} al subir el documento`));
      }
    };

    xhr.onerror = () => reject(new Error("Error de red al subir el documento"));

    xhr.send(formData);
  });
}

export async function getDocumentStatus(documentId: string): Promise<DocumentStatusResponse> {
  const res = await fetch(`${API_URL}/documents/${documentId}/status`);
  if (!res.ok) {
    throw new Error(`Error ${res.status} al consultar el estado del documento`);
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
  model: string;
}

export interface ErrorDocumentResponse {
  id: string;
  filename: string;
  format: string;
  error_message: string | null;
}

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${API_URL}${path}`);
  if (!res.ok) {
    throw new Error(`Error ${res.status} al consultar ${path}`);
  }
  return res.json();
}

export function getStatsByFormat(): Promise<Record<string, number>> {
  return getJson("/stats/by-format");
}

export function getStatsByStatus(): Promise<Record<string, number>> {
  return getJson("/stats/by-status");
}

export function getStatsErrors(): Promise<ErrorDocumentResponse[]> {
  return getJson("/stats/errors");
}

export function getStatsTimeline(): Promise<Record<string, number>> {
  return getJson("/stats/timeline");
}

export function getStatsByTag(): Promise<Record<string, number>> {
  return getJson("/stats/by-tag");
}

export async function sendChatMessage(message: string, model: string): Promise<ChatApiResponse> {
  const res = await fetch(`${API_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, model }),
  });
  if (!res.ok) {
    throw new Error(`Error ${res.status} al consultar el backend`);
  }
  return res.json();
}
