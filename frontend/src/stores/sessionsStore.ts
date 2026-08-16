import { create } from "zustand";
import * as api from "../services/api";
import { useChatStore } from "./chatStore";

export interface Session {
  id: string;
  title: string;
  updatedAt: string;
}

function fromApi(s: api.SessionApiResponse): Session {
  return { id: s.id, title: s.title ?? "Nueva conversación", updatedAt: s.updated_at };
}

interface SessionsState {
  sessions: Session[];
  activeId: string;
  loaded: boolean;
  init: () => Promise<void>;
  setActive: (id: string) => void;
  renameSession: (id: string, title: string) => void;
  deleteSession: (id: string) => Promise<void>;
  createSession: () => Promise<void>;
}

export const useSessionsStore = create<SessionsState>((set, get) => ({
  sessions: [],
  activeId: "",
  loaded: false,
  init: async () => {
    if (get().loaded) return;
    set({ loaded: true });

    let sessions = (await api.listSessions()).map(fromApi);
    if (sessions.length === 0) {
      sessions = [fromApi(await api.createSession())];
    }
    set({ sessions, activeId: sessions[0].id });
  },
  setActive: (id) => set({ activeId: id }),
  renameSession: (id, title) =>
    set((state) => ({
      sessions: state.sessions.map((s) =>
        s.id === id ? { ...s, title: title.trim() || "(sin título)" } : s
      ),
    })),
  deleteSession: async (id) => {
    await api.deleteSession(id);

    const { sessions: current, activeId: currentActiveId } = get();
    let sessions = current.filter((s) => s.id !== id);
    let activeId = currentActiveId;

    if (sessions.length === 0) {
      const fresh = fromApi(await api.createSession());
      sessions = [fresh];
      activeId = fresh.id;
    } else if (currentActiveId === id) {
      activeId = sessions[0].id;
    }
    set({ sessions, activeId });
  },
  createSession: async () => {
    const { activeId, sessions } = get();
    if (sessions.some((s) => s.id === activeId)) {
      await useChatStore.getState().loadMessages(activeId);
      const activeIsEmpty = (useChatStore.getState().messagesBySession[activeId] ?? []).length === 0;
      if (activeIsEmpty) return;
    }

    const fresh = fromApi(await api.createSession());
    set((state) => ({ sessions: [fresh, ...state.sessions], activeId: fresh.id }));
  },
}));
