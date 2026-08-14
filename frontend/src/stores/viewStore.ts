import { create } from "zustand";

export type View = "chat" | "stats";

interface ViewState {
  view: View;
  setView: (view: View) => void;
}

export const useViewStore = create<ViewState>((set) => ({
  view: "chat",
  setView: (view) => set({ view }),
}));
