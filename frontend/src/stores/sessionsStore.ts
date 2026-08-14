import { create } from "zustand";

export interface Session {
  id: string;
  title: string;
  tag: string;
  time: string;
}

const initialSessions: Session[] = [
  { id: "s5", title: "Cláusulas de rescisión — Proveedora Ibérica", tag: "legal", time: "hoy" },
  { id: "s4", title: "Modelo Ollama: qwen2.5 vs llama3.1", tag: "técnico", time: "ayer" },
  { id: "s3", title: "Resumen informe financiero Q3", tag: "financiero", time: "2 días" },
  { id: "s2", title: "Política de vacaciones 2026", tag: "rrhh", time: "5 días" },
  { id: "s1", title: "Roadmap de producto — presentación", tag: "marketing", time: "6 días" },
];

interface SessionsState {
  sessions: Session[];
  activeId: string;
  setActive: (id: string) => void;
  renameSession: (id: string, title: string) => void;
  deleteSession: (id: string) => void;
}

export const useSessionsStore = create<SessionsState>((set) => ({
  sessions: initialSessions,
  activeId: initialSessions[0].id,
  setActive: (id) => set({ activeId: id }),
  renameSession: (id, title) =>
    set((state) => ({
      sessions: state.sessions.map((s) =>
        s.id === id ? { ...s, title: title.trim() || "(sin título)" } : s
      ),
    })),
  deleteSession: (id) =>
    set((state) => {
      const sessions = state.sessions.filter((s) => s.id !== id);
      const activeId =
        state.activeId === id ? sessions[0]?.id ?? "" : state.activeId;
      return { sessions, activeId };
    }),
}));
