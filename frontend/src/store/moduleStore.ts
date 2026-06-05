// Enabled-modules state via Zustand. The nav and feature routes render strictly
// from this list, so a disabled module is invisible (section 7) - no greyed-out
// links, no "coming soon".

import { create } from "zustand";
import * as api from "@/api/endpoints";
import type { ModuleKey } from "@/api/types";

interface ModuleState {
  enabled: Set<ModuleKey>;
  loaded: boolean;
  load: () => Promise<void>;
  isEnabled: (key: ModuleKey) => boolean;
}

export const useModuleStore = create<ModuleState>((set, get) => ({
  enabled: new Set<ModuleKey>(),
  loaded: false,

  load: async () => {
    try {
      const keys = await api.getEnabledModules();
      set({ enabled: new Set(keys), loaded: true });
    } catch {
      set({ enabled: new Set<ModuleKey>(), loaded: true });
    }
  },

  isEnabled: (key) => get().enabled.has(key),
}));
