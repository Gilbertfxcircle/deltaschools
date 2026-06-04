// Auth state via Zustand. Holds the decoded identity (id/email/role/permissions)
// and exposes a permission check used by route guards and nav gating. Tokens
// live in tokenStore (localStorage, per-tenant namespaced); this store mirrors
// the derived identity for the UI.

import { create } from "zustand";
import { decodeAccessClaims, isExpired } from "@/api/jwt";
import { tokenStore } from "@/api/tokenStore";
import { hasPermission } from "@/lib/permissions";
import * as api from "@/api/endpoints";
import type { LoginPayload } from "@/api/endpoints";

export interface Identity {
  id: string;
  email: string;
  role: string;
  tenant: string | null;
  permissions: string[];
}

interface AuthState {
  identity: Identity | null;
  initialized: boolean;
  login: (payload: LoginPayload) => Promise<void>;
  logout: () => Promise<void>;
  hydrate: () => void;
  can: (permission: string) => boolean;
  isAuthenticated: () => boolean;
}

function identityFromToken(token: string | null): Identity | null {
  if (!token) {
    return null;
  }
  const claims = decodeAccessClaims(token);
  if (!claims || isExpired(claims)) {
    return null;
  }
  return {
    id: claims.sub,
    email: claims.email,
    role: claims.role,
    tenant: claims.tenant,
    permissions: claims.permissions ?? [],
  };
}

export const useAuthStore = create<AuthState>((set, get) => ({
  identity: null,
  initialized: false,

  hydrate: () => {
    const identity = identityFromToken(tokenStore.getAccess());
    set({ identity, initialized: true });
  },

  login: async (payload) => {
    const tokens = await api.login(payload);
    tokenStore.set(tokens.access_token, tokens.refresh_token);
    set({ identity: identityFromToken(tokens.access_token), initialized: true });
  },

  logout: async () => {
    try {
      await api.logout();
    } catch {
      // best-effort; clear locally regardless
    }
    tokenStore.clear();
    set({ identity: null });
  },

  can: (permission) => {
    const id = get().identity;
    return id ? hasPermission(id.permissions, permission) : false;
  },

  isAuthenticated: () => get().identity !== null,
}));
