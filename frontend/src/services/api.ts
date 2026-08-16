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

export interface ChatDoneEvent {
  sources: SourceResponse[];
  model: string;
}

export interface ChatStreamHandlers {
  onChunk: (text: string) => void;
  onDone: (payload: ChatDoneEvent) => void;
  onError: (message: string) => void;
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

function parseSseFrame(frame: string): { event: string; data: unknown } | null {
  if (!frame.trim()) return null;
  const [eventLine, dataLine] = frame.split("\n");
  return {
    event: eventLine.replace(/^event: /, ""),
    data: JSON.parse(dataLine.replace(/^data: /, "")),
  };
}

export async function sendChatMessage(
  message: string,
  sessionId: string,
  model: string,
  handlers: ChatStreamHandlers,
  signal?: AbortSignal,
): Promise<void> {
  const res = await fetch(`${API_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, session_id: sessionId, model }),
    signal,
  });
  if (!res.ok || !res.body) {
    throw new Error(`Error ${res.status} al consultar el backend`);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    let separatorIndex: number;
    while ((separatorIndex = buffer.indexOf("\n\n")) !== -1) {
      const frame = buffer.slice(0, separatorIndex);
      buffer = buffer.slice(separatorIndex + 2);
      const parsed = parseSseFrame(frame);
      if (!parsed) continue;

      if (parsed.event === "chunk") {
        handlers.onChunk(parsed.data as string);
      } else if (parsed.event === "done") {
        handlers.onDone(parsed.data as ChatDoneEvent);
      } else if (parsed.event === "error") {
        handlers.onError((parsed.data as { message: string }).message);
      }
    }
  }
}

export interface SessionApiResponse {
  id: string;
  title: string | null;
  created_at: string;
  updated_at: string;
}

export interface MessageApiResponse {
  id: string;
  role: string;
  content: string;
  created_at: string;
  model_used: string | null;
  sources: string | null;
}

export async function listSessions(): Promise<SessionApiResponse[]> {
  return getJson("/sessions");
}

export async function createSession(): Promise<SessionApiResponse> {
  const res = await fetch(`${API_URL}/sessions`, { method: "POST" });
  if (!res.ok) {
    throw new Error(`Error ${res.status} al crear la sesión`);
  }
  return res.json();
}

export async function getSessionMessages(sessionId: string): Promise<MessageApiResponse[]> {
  return getJson(`/sessions/${sessionId}/messages`);
}

export async function deleteSession(sessionId: string): Promise<void> {
  const res = await fetch(`${API_URL}/sessions/${sessionId}`, { method: "DELETE" });
  if (!res.ok) {
    throw new Error(`Error ${res.status} al eliminar la sesión`);
  }
}

export interface DocumentListItem {
  id: string;
  status: string;
  filename: string;
  format: string;
  size_bytes: number | null;
  tags: string[];
  absolute_path: string | null;
  uploaded_at: string;
}

export async function listDocuments(): Promise<DocumentListItem[]> {
  const { documents } = await getJson<{ documents: DocumentListItem[] }>("/documents");
  return documents;
}

export async function deleteDocument(documentId: string): Promise<void> {
  const res = await fetch(`${API_URL}/documents/${documentId}`, { method: "DELETE" });
  if (!res.ok) {
    throw new Error(`Error ${res.status} al eliminar el documento`);
  }
}

export function getDocumentFileUrl(documentId: string): string {
  return `${API_URL}/documents/${documentId}/file`;
}
