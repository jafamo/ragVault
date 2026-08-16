import { create } from "zustand";
import { useChatStore } from "./chatStore";

export interface Session {
  id: string;
  title: string;
  tag: string;
  time: string;
}

let sessionCounter = 0;
function nextSessionId() {
  sessionCounter += 1;
  return `local-session-${sessionCounter}`;
}

function blankSession(): Session {
  return { id: nextSessionId(), title: "Nueva conversación", tag: "", time: "ahora" };
}

interface SessionsState {
  sessions: Session[];
  activeId: string;
  setActive: (id: string) => void;
  renameSession: (id: string, title: string) => void;
  deleteSession: (id: string) => void;
  createSession: () => void;
}

const initialSession = blankSession();

export const useSessionsStore = create<SessionsState>((set, get) => ({
  sessions: [initialSession],
  activeId: initialSession.id,
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
      if (sessions.length === 0) {
        const fresh = blankSession();
        return { sessions: [fresh], activeId: fresh.id };
      }
      const activeId =
        state.activeId === id ? sessions[0].id : state.activeId;
      return { sessions, activeId };
    }),
  createSession: () => {
    const { activeId, sessions } = get();
    const activeIsEmpty = (useChatStore.getState().messagesBySession[activeId] ?? []).length === 0;
    if (activeIsEmpty && sessions.some((s) => s.id === activeId)) return;

    const fresh = blankSession();
    set((state) => ({ sessions: [fresh, ...state.sessions], activeId: fresh.id }));
  },
}));
