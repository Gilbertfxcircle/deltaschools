// Authenticated shell: branded sidebar nav (module + permission gated) + header.

import { Link, Outlet, useLocation, useNavigate } from "react-router-dom";
import { useMemo } from "react";
import { useAuthStore } from "@/store/authStore";
import { useModuleStore } from "@/store/moduleStore";
import { NAV_ITEMS, visibleNav } from "@/nav/navConfig";
import type { ModuleKey } from "@/api/types";

export function AppLayout(): JSX.Element {
  const location = useLocation();
  const navigate = useNavigate();
  const identity = useAuthStore((s) => s.identity);
  const can = useAuthStore((s) => s.can);
  const logout = useAuthStore((s) => s.logout);
  const isEnabled = useModuleStore((s) => s.isEnabled);

  const items = useMemo(
    () =>
      visibleNav(NAV_ITEMS, {
        isModuleEnabled: (k: ModuleKey) => isEnabled(k),
        can,
      }),
    [isEnabled, can],
  );

  async function handleLogout(): Promise<void> {
    await logout();
    navigate("/login", { replace: true });
  }

  return (
    <div className="flex h-full">
      <aside className="w-60 shrink-0 bg-white border-r border-slate-200 flex flex-col">
        <div
          className="px-4 py-4 text-white font-semibold"
          style={{ background: "var(--brand-primary)" }}
        >
          Delta Plax
        </div>
        <nav className="flex-1 overflow-y-auto py-2">
          {items.map((item) => {
            const active = location.pathname === item.path;
            return (
              <Link
                key={item.key}
                to={item.path}
                className={[
                  "block px-4 py-2 text-sm",
                  active ? "bg-slate-100 font-medium text-slate-900" : "text-slate-600",
                ].join(" ")}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>
        <button
          onClick={handleLogout}
          className="m-3 rounded px-3 py-2 text-sm text-white"
          style={{ background: "var(--brand-secondary)" }}
        >
          Sign out
        </button>
      </aside>

      <div className="flex-1 flex flex-col">
        <header className="h-14 bg-white border-b border-slate-200 flex items-center justify-between px-6">
          <span className="text-sm text-slate-500">
            {identity?.tenant ? `Tenant: ${identity.tenant}` : "Platform"}
          </span>
          <span className="text-sm text-slate-700">
            {identity?.email} &middot; {identity?.role}
          </span>
        </header>
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
        <footer className="px-6 py-3 text-xs text-slate-400 border-t border-slate-200">
          &copy; 2026&ndash;2035 Delta Plax Technologies
        </footer>
      </div>
    </div>
  );
}
