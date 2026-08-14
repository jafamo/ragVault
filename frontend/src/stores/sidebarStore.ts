import { create } from "zustand";
import { persist } from "zustand/middleware";

interface SidebarState {
  historyCollapsed: boolean;
  toggleHistoryCollapsed: () => void;
  setHistoryCollapsed: (collapsed: boolean) => void;
}

export const useSidebarStore = create<SidebarState>()(
  persist(
    (set) => ({
      historyCollapsed: false,
      toggleHistoryCollapsed: () =>
        set((state) => ({ historyCollapsed: !state.historyCollapsed })),
      setHistoryCollapsed: (collapsed) => set({ historyCollapsed: collapsed }),
    }),
    { name: "ragvault-sidebar" },
  ),
);
