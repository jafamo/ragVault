import { create } from "zustand";
import { getSessionMessages, sendChatMessage, type MessageApiResponse } from "../services/api";
import { useModelStore } from "./modelStore";

export interface Source {
  doc: string;
  page: string;
  score: number;
}

export interface Message {
  id: string;
  role: "user" | "assistant" | "system" | "error";
  text: string;
  meta: string;
  sources?: Source[];
}

let counter = 0;
function nextId() {
  counter += 1;
  return `local-${counter}`;
}

function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString("es-ES", { hour: "2-digit", minute: "2-digit" });
}

function fromApiMessage(m: MessageApiResponse): Message {
  const time = formatTime(m.created_at);
  if (m.role === "user") {
    return { id: m.id, role: "user", text: m.content, meta: `tú · ${time}` };
  }
  const sources: Source[] = m.sources
    ? (JSON.parse(m.sources).chunks_used ?? []).map(
        (s: { document_name: string; page: number | null; similarity_score: number }) => ({
          doc: s.document_name,
          page: s.page != null ? `pág. ${s.page}` : "—",
          score: s.similarity_score,
        })
      )
    : undefined;
  return {
    id: m.id,
    role: "assistant",
    text: m.content,
    meta: `${m.model_used ?? "?"} · ${time}`,
    sources,
  };
}

function appendMessage(
  messagesBySession: Record<string, Message[]>,
  sessionId: string,
  message: Message
): Record<string, Message[]> {
  const existing = messagesBySession[sessionId] ?? [];
  return { ...messagesBySession, [sessionId]: [...existing, message] };
}

interface ChatState {
  messagesBySession: Record<string, Message[]>;
  loadedSessions: Record<string, boolean>;
  pendingSessionId: string | null;
  loadMessages: (sessionId: string) => Promise<void>;
  sendMessage: (sessionId: string, text: string) => Promise<void>;
}

export const useChatStore = create<ChatState>((set, get) => ({
  messagesBySession: {},
  loadedSessions: {},
  pendingSessionId: null,
  loadMessages: async (sessionId) => {
    if (get().loadedSessions[sessionId]) return;
    set((state) => ({ loadedSessions: { ...state.loadedSessions, [sessionId]: true } }));

    const messages = (await getSessionMessages(sessionId)).map(fromApiMessage);
    set((state) => ({
      messagesBySession: { ...state.messagesBySession, [sessionId]: messages },
    }));
  },
  sendMessage: async (sessionId, text) => {
    const trimmed = text.trim();
    if (!trimmed) return;

    const userMessage: Message = {
      id: nextId(),
      role: "user",
      text: trimmed,
      meta: "tú · ahora",
    };
    set((state) => ({
      messagesBySession: appendMessage(state.messagesBySession, sessionId, userMessage),
      pendingSessionId: sessionId,
    }));

    try {
      const model = useModelStore.getState().model;
      const response = await sendChatMessage(trimmed, sessionId, model);
      const assistantMessage: Message = {
        id: nextId(),
        role: "assistant",
        text: response.answer,
        meta: `${response.model} · ahora`,
        sources: response.sources.map((s) => ({
          doc: s.document_name,
          page: s.page != null ? `pág. ${s.page}` : "—",
          score: s.similarity_score,
        })),
      };
      set((state) => ({
        messagesBySession: appendMessage(state.messagesBySession, sessionId, assistantMessage),
      }));
    } catch (err) {
      const errorMessage: Message = {
        id: nextId(),
        role: "error",
        text:
          err instanceof Error
            ? err.message
            : "No se pudo contactar con el backend. Inténtalo de nuevo.",
        meta: "error",
      };
      set((state) => ({
        messagesBySession: appendMessage(state.messagesBySession, sessionId, errorMessage),
      }));
    } finally {
      if (get().pendingSessionId === sessionId) {
        set({ pendingSessionId: null });
      }
    }
  },
}));
