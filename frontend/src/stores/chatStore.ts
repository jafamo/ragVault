import { create } from "zustand";

export interface Source {
  doc: string;
  page: string;
  score: number;
}

export interface Message {
  id: string;
  role: "user" | "assistant" | "system";
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

interface ChatState {
  messagesBySession: Record<string, Message[]>;
  sendMessage: (sessionId: string, text: string) => void;
}

export const useChatStore = create<ChatState>((set) => ({
  messagesBySession: initialMessages,
  sendMessage: (sessionId, text) =>
    set((state) => {
      const trimmed = text.trim();
      if (!trimmed) return state;
      const existing = state.messagesBySession[sessionId] ?? [];
      const userMessage: Message = {
        id: nextId(),
        role: "user",
        text: trimmed,
        meta: "tú · ahora",
      };
      const systemMessage: Message = {
        id: nextId(),
        role: "system",
        text: "Vista previa — sin pipeline RAG conectado todavía.",
        meta: "sistema",
      };
      return {
        messagesBySession: {
          ...state.messagesBySession,
          [sessionId]: [...existing, userMessage, systemMessage],
        },
      };
    }),
}));
