// Dashboard: shows the authenticated identity and the set of enabled modules
// (proof that nav/features are module-driven).

import { useEffect } from "react";
import { useAuthStore } from "@/store/authStore";
import { useModuleStore } from "@/store/moduleStore";
import { Card, PageTitle } from "@/components/ui";

export function DashboardPage(): JSX.Element {
  const identity = useAuthStore((s) => s.identity);
  const enabled = useModuleStore((s) => s.enabled);
  const loaded = useModuleStore((s) => s.loaded);
  const load = useModuleStore((s) => s.load);

  useEffect(() => {
    if (!loaded) {
      void load();
    }
  }, [loaded, load]);

  return (
    <div>
      <PageTitle>Dashboard</PageTitle>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <Card>
          <h2 className="mb-2 text-sm font-semibold text-slate-700">Signed in as</h2>
          <dl className="space-y-1 text-sm text-slate-600">
            <div>Email: {identity?.email}</div>
            <div>Role: {identity?.role}</div>
            <div>Tenant: {identity?.tenant ?? "(platform)"}</div>
          </dl>
        </Card>
        <Card>
          <h2 className="mb-2 text-sm font-semibold text-slate-700">Enabled modules</h2>
          {enabled.size === 0 ? (
            <p className="text-sm text-slate-500">No optional modules enabled.</p>
          ) : (
            <ul className="flex flex-wrap gap-2">
              {[...enabled].map((m) => (
                <li
                  key={m}
                  className="rounded-full px-3 py-1 text-xs text-white"
                  style={{ background: "var(--brand-secondary)" }}
                >
                  {m}
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>
    </div>
  );
}
