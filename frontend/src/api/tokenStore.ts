// Token persistence. Kept in a single module so the axios interceptors and the
// auth store share one source of truth. Tokens are namespaced per-tenant so
// switching tenants in the same browser never reuses another school's session.

import { resolveTenant } from "@/api/tenant";

const ACCESS_PREFIX = "deltaplax.access.";
const REFRESH_PREFIX = "deltaplax.refresh.";

function key(prefix: string): string {
  return `${prefix}${resolveTenant() ?? "_platform"}`;
}

export const tokenStore = {
  getAccess(): string | null {
    return localStorage.getItem(key(ACCESS_PREFIX));
  },
  getRefresh(): string | null {
    return localStorage.getItem(key(REFRESH_PREFIX));
  },
  set(access: string, refresh?: string): void {
    localStorage.setItem(key(ACCESS_PREFIX), access);
    if (refresh) {
      localStorage.setItem(key(REFRESH_PREFIX), refresh);
    }
  },
  clear(): void {
    localStorage.removeItem(key(ACCESS_PREFIX));
    localStorage.removeItem(key(REFRESH_PREFIX));
  },
};
