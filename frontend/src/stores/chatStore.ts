import { create } from "zustand";
import {
  getSessionMessages,
  sendChatMessage,
  type ChatDoneEvent,
  type MessageApiResponse,
} from "../services/api";
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
  streaming?: boolean;
}

function sourcesFromDoneEvent(payload: ChatDoneEvent): Source[] {
  return payload.sources.map((s) => ({
    doc: s.document_name,
    page: s.page != null ? `pág. ${s.page}` : "—",
    score: s.similarity_score,
  }));
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

function updateMessage(
  messagesBySession: Record<string, Message[]>,
  sessionId: string,
  messageId: string,
  update: (message: Message) => Message
): Record<string, Message[]> {
  const existing = messagesBySession[sessionId] ?? [];
  return {
    ...messagesBySession,
    [sessionId]: existing.map((m) => (m.id === messageId ? update(m) : m)),
  };
}

interface ChatState {
  messagesBySession: Record<string, Message[]>;
  loadedSessions: Record<string, boolean>;
  pendingSessionId: string | null;
  streamControllers: Record<string, AbortController>;
  loadMessages: (sessionId: string) => Promise<void>;
  sendMessage: (sessionId: string, text: string) => Promise<void>;
  cancelStream: (sessionId: string) => void;
}

export const useChatStore = create<ChatState>((set, get) => ({
  messagesBySession: {},
  loadedSessions: {},
  pendingSessionId: null,
  streamControllers: {},
  cancelStream: (sessionId) => {
    get().streamControllers[sessionId]?.abort();
  },
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
    const assistantId = nextId();
    const assistantMessage: Message = {
      id: assistantId,
      role: "assistant",
      text: "",
      meta: "ahora",
      streaming: true,
    };
    set((state) => ({
      messagesBySession: appendMessage(
        appendMessage(state.messagesBySession, sessionId, userMessage),
        sessionId,
        assistantMessage
      ),
      pendingSessionId: sessionId,
    }));

    const controller = new AbortController();
    set((state) => ({
      streamControllers: { ...state.streamControllers, [sessionId]: controller },
    }));

    try {
      const model = useModelStore.getState().model;
      await sendChatMessage(
        trimmed,
        sessionId,
        model,
        {
          onChunk: (piece) => {
            set((state) => ({
              messagesBySession: updateMessage(state.messagesBySession, sessionId, assistantId, (m) => ({
                ...m,
                text: m.text + piece,
              })),
            }));
          },
          onDone: (payload) => {
            set((state) => ({
              messagesBySession: updateMessage(state.messagesBySession, sessionId, assistantId, (m) => ({
                ...m,
                meta: `${payload.model} · ahora`,
                sources: sourcesFromDoneEvent(payload),
                streaming: false,
              })),
            }));
          },
          onError: (message) => {
            set((state) => ({
              messagesBySession: updateMessage(state.messagesBySession, sessionId, assistantId, (m) => ({
                ...m,
                role: "error",
                text: m.text ? `${m.text}\n\n${message}` : message,
                meta: "error",
                streaming: false,
              })),
            }));
          },
        },
        controller.signal
      );
    } catch (err) {
      if (err instanceof DOMException && err.name === "AbortError") {
        return;
      }
      const errorText =
        err instanceof Error
          ? err.message
          : "No se pudo contactar con el backend. Inténtalo de nuevo.";
      set((state) => ({
        messagesBySession: updateMessage(state.messagesBySession, sessionId, assistantId, (m) => ({
          ...m,
          role: "error",
          text: errorText,
          meta: "error",
          streaming: false,
        })),
      }));
    } finally {
      set((state) => {
        const { [sessionId]: _removed, ...rest } = state.streamControllers;
        return {
          streamControllers: rest,
          pendingSessionId: state.pendingSessionId === sessionId ? null : state.pendingSessionId,
        };
      });
    }
  },
}));
