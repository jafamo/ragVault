import { create } from "zustand";
import { DEFAULT_MODEL } from "../data/mockModels";

interface ModelState {
  model: string;
  models: string[];
  setModel: (model: string) => void;
  setAvailableModels: (models: string[], defaultModel: string) => void;
}

export const useModelStore = create<ModelState>((set) => ({
  model: DEFAULT_MODEL,
  models: [DEFAULT_MODEL],
  setModel: (model) => set({ model }),
  setAvailableModels: (models, defaultModel) => set({ models, model: defaultModel }),
}));
