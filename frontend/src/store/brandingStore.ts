// Branding state via Zustand. Loads the current tenant's branding once and
// applies it to the document. Resets to defaults when there is no tenant
// (platform/admin host) so the platform UI never inherits a school's theme.

import { create } from "zustand";
import * as api from "@/api/endpoints";
import { applyBranding, resetBranding } from "@/branding/applyBranding";
import { resolveTenant } from "@/api/tenant";
import type { Branding } from "@/api/types";

interface BrandingState {
  branding: Branding;
  loaded: boolean;
  load: () => Promise<void>;
}

export const useBrandingStore = create<BrandingState>((set) => ({
  branding: {},
  loaded: false,

  load: async () => {
    const tenant = resolveTenant();
    if (!tenant) {
      resetBranding();
      set({ branding: {}, loaded: true });
      return;
    }
    try {
      const branding = await api.getBranding();
      applyBranding(branding);
      set({ branding, loaded: true });
    } catch {
      // Branding must never block app load; fall back to defaults.
      resetBranding();
      set({ branding: {}, loaded: true });
    }
  },
}));
