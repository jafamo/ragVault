import { create } from "zustand";

export type Skin = "ledger" | "terminal";
export type Mode = "light" | "dark" | null;

interface ThemeState {
  skin: Skin;
  mode: Mode;
  setSkin: (skin: Skin) => void;
  setMode: (mode: Mode) => void;
}

export const useThemeStore = create<ThemeState>((set) => ({
  skin: "ledger",
  mode: null,
  setSkin: (skin) => set({ skin }),
  setMode: (mode) =>
    set((state) => ({ mode: state.mode === mode ? null : mode })),
}));
