// Approvals: a director/registrar reviews pending protected-data change
// requests and approves/rejects them (section 4.4). The server applies the
// change only on approval and audits both the request and the outcome.

import { useEffect, useState } from "react";
import * as api from "@/api/endpoints";
import type { ApprovalRequestSummary } from "@/api/types";
import { Button, Card, ErrorText, PageTitle } from "@/components/ui";
import { toMessage } from "@/lib/errors";

export function ApprovalsPage(): JSX.Element {
  const [items, setItems] = useState<ApprovalRequestSummary[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [actingId, setActingId] = useState<string | null>(null);

  async function refresh(): Promise<void> {
    setLoading(true);
    setError("");
    try {
      setItems(await api.listApprovals());
    } catch (err) {
      setError(toMessage(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  async function decide(id: string, decision: "approved" | "rejected"): Promise<void> {
    setActingId(id);
    setError("");
    try {
      await api.decideApproval(id, decision);
      await refresh();
    } catch (err) {
      setError(toMessage(err));
    } finally {
      setActingId(null);
    }
  }

  return (
    <div className="space-y-5">
      <PageTitle>Approval requests</PageTitle>
      <ErrorText>{error}</ErrorText>
      <Card>
        {loading ? (
          <p className="text-sm text-slate-500">Loading...</p>
        ) : items.length === 0 ? (
          <p className="text-sm text-slate-500">No pending requests.</p>
        ) : (
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-slate-500">
                <th className="py-2">Resource</th>
                <th className="py-2">Reason</th>
                <th className="py-2">State</th>
                <th className="py-2 text-right">Action</th>
              </tr>
            </thead>
            <tbody>
              {items.map((r) => (
                <tr key={r.id} className="border-b border-slate-100">
                  <td className="py-2">{r.resource}</td>
                  <td className="py-2">{r.reason}</td>
                  <td className="py-2">{r.state}</td>
                  <td className="py-2 text-right">
                    {r.state === "pending" ? (
                      <span className="inline-flex gap-2">
                        <Button
                          onClick={() => decide(r.id, "approved")}
                          disabled={actingId === r.id}
                        >
                          Approve
                        </Button>
                        <button
                          onClick={() => decide(r.id, "rejected")}
                          disabled={actingId === r.id}
                          className="rounded px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
                          style={{ background: "#b91c1c" }}
                        >
                          Reject
                        </button>
                      </span>
                    ) : (
                      <span className="text-slate-400">&mdash;</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>
    </div>
  );
}
