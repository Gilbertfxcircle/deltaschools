// Billing page: shows the school's finance summary and lets finance staff look
// up a student's invoices and record a payment. Balances/statuses come straight
// from the backend's pure finance logic.

import { useEffect, useState, type FormEvent } from "react";
import * as api from "@/api/endpoints";
import type { FinanceSummary, InvoiceSummary } from "@/api/endpoints";
import { useAuthStore } from "@/store/authStore";
import { Button, Card, ErrorText, Input, PageTitle } from "@/components/ui";
import { toMessage } from "@/lib/errors";

export function BillingPage(): JSX.Element {
  const can = useAuthStore((s) => s.can);
  const canWrite = can("finance:write");

  const [summary, setSummary] = useState<FinanceSummary | null>(null);
  const [studentId, setStudentId] = useState("");
  const [invoices, setInvoices] = useState<InvoiceSummary[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        setSummary(await api.financeSummary());
      } catch (err) {
        setError(toMessage(err));
      }
    })();
  }, []);

  async function lookup(e: FormEvent): Promise<void> {
    e.preventDefault();
    if (!studentId) {
      return;
    }
    setBusy(true);
    setError("");
    try {
      setInvoices(await api.studentInvoices(studentId));
    } catch (err) {
      setError(toMessage(err));
    } finally {
      setBusy(false);
    }
  }

  async function pay(invoice: InvoiceSummary): Promise<void> {
    setError("");
    try {
      await api.recordPayment({
        invoice_id: invoice.id,
        student_id: studentId,
        amount: invoice.balance,
        method: "cash",
      });
      setInvoices(await api.studentInvoices(studentId));
      setSummary(await api.financeSummary());
    } catch (err) {
      setError(toMessage(err));
    }
  }

  return (
    <div className="space-y-5">
      <PageTitle>Billing</PageTitle>
      <ErrorText>{error}</ErrorText>

      {summary && (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          <Card>
            <p className="text-xs text-slate-500">Total billed</p>
            <p className="text-lg font-semibold">{summary.total_billed.toFixed(2)}</p>
          </Card>
          <Card>
            <p className="text-xs text-slate-500">Collected</p>
            <p className="text-lg font-semibold">{summary.total_collected.toFixed(2)}</p>
          </Card>
          <Card>
            <p className="text-xs text-slate-500">Outstanding</p>
            <p className="text-lg font-semibold">{summary.total_outstanding.toFixed(2)}</p>
          </Card>
        </div>
      )}

      <Card>
        <h2 className="mb-3 text-sm font-semibold text-slate-700">Student invoices</h2>
        <form onSubmit={lookup} className="mb-4 flex gap-2">
          <Input
            placeholder="Student ID"
            value={studentId}
            onChange={(e) => setStudentId(e.target.value)}
          />
          <Button type="submit" disabled={busy}>
            {busy ? "..." : "Look up"}
          </Button>
        </form>
        {invoices.length === 0 ? (
          <p className="text-sm text-slate-500">No invoices to show.</p>
        ) : (
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-slate-500">
                <th className="py-2">Amount</th>
                <th className="py-2">Balance</th>
                <th className="py-2">Status</th>
                {canWrite && <th className="py-2 text-right">Action</th>}
              </tr>
            </thead>
            <tbody>
              {invoices.map((inv) => (
                <tr key={inv.id} className="border-b border-slate-100">
                  <td className="py-2">{inv.amount.toFixed(2)}</td>
                  <td className="py-2">{inv.balance.toFixed(2)}</td>
                  <td className="py-2">{inv.status}</td>
                  {canWrite && (
                    <td className="py-2 text-right">
                      {inv.balance > 0 ? (
                        <Button onClick={() => pay(inv)}>Pay balance</Button>
                      ) : (
                        <span className="text-slate-400">&mdash;</span>
                      )}
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>
    </div>
  );
}
