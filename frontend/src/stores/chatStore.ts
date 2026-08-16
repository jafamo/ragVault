import { create } from "zustand";
import { sendChatMessage } from "../services/api";
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

const initialMessages: Record<string, Message[]> = {
  s5: [
    {
      id: "m1",
      role: "user",
      text: "¿Cuáles son las condiciones de rescisión anticipada del contrato con Proveedora Ibérica?",
      meta: "tú · 11:42",
    },
    {
      id: "m2",
      role: "assistant",
      text: "Cualquiera de las partes puede rescindir con un preaviso mínimo de 90 días. La parte que rescinda sin causa justificada antes de los 12 primeros meses abonará una penalización del 15% del importe anual pactado.",
      meta: "qwen2.5:14b · 11:42",
      sources: [
        { doc: "contrato_proveedora_iberica.pdf", page: "pág. 4", score: 0.91 },
        { doc: "anexo_penalizaciones_2025.pdf", page: "pág. 1", score: 0.78 },
      ],
    },
  ],
};

let counter = 0;
function nextId() {
  counter += 1;
  return `local-${counter}`;
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
  pendingSessionId: string | null;
  sendMessage: (sessionId: string, text: string) => Promise<void>;
}

export const useChatStore = create<ChatState>((set, get) => ({
  messagesBySession: initialMessages,
  pendingSessionId: null,
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
      const response = await sendChatMessage(trimmed, model);
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
