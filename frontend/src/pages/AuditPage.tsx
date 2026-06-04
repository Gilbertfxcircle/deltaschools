// Audit log viewer (read-only). The backend exposes no write/delete route and
// the records are immutable at the DB level; this page just lists them.

import { useEffect, useState } from "react";
import * as api from "@/api/endpoints";
import type { AuditEntry } from "@/api/types";
import { Card, ErrorText, PageTitle } from "@/components/ui";
import { toMessage } from "@/lib/errors";

export function AuditPage(): JSX.Element {
  const [entries, setEntries] = useState<AuditEntry[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        setEntries(await api.listAudit(100));
      } catch (err) {
        setError(toMessage(err));
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  return (
    <div className="space-y-5">
      <PageTitle>Audit log</PageTitle>
      <ErrorText>{error}</ErrorText>
      <Card>
        {loading ? (
          <p className="text-sm text-slate-500">Loading...</p>
        ) : entries.length === 0 ? (
          <p className="text-sm text-slate-500">No audit entries.</p>
        ) : (
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-slate-500">
                <th className="py-2">Time</th>
                <th className="py-2">User</th>
                <th className="py-2">Action</th>
                <th className="py-2">Resource</th>
                <th className="py-2">Status</th>
              </tr>
            </thead>
            <tbody>
              {entries.map((e) => (
                <tr key={e.id} className="border-b border-slate-100">
                  <td className="py-2">{e.timestamp ?? "-"}</td>
                  <td className="py-2">{e.user_email}</td>
                  <td className="py-2">{e.action}</td>
                  <td className="py-2">
                    {e.resource}
                    {e.resource_id ? ` (${e.resource_id.slice(0, 8)})` : ""}
                  </td>
                  <td className="py-2">{e.approval_status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>
    </div>
  );
}
