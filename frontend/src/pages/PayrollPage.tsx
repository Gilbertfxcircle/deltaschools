// Payroll: run a payslip (progressive PAYE computed server-side) and view the
// payroll history. Protected financial data; gated by payroll permissions.

import { useEffect, useState, type FormEvent } from "react";
import * as api from "@/api/endpoints";
import type { PayrollItem } from "@/api/endpoints";
import { useAuthStore } from "@/store/authStore";
import { Button, Card, DataTable, ErrorText, Input, PageTitle } from "@/components/ui";
import { toMessage } from "@/lib/errors";

export function PayrollPage(): JSX.Element {
  const can = useAuthStore((s) => s.can);
  const canWrite = can("payroll:write");

  const [rows, setRows] = useState<PayrollItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [staffId, setStaffId] = useState("");
  const [period, setPeriod] = useState(new Date().toISOString().slice(0, 7));
  const [gross, setGross] = useState("");
  const [allowances, setAllowances] = useState("");
  const [deductions, setDeductions] = useState("");
  const [saving, setSaving] = useState(false);

  async function refresh(): Promise<void> {
    setLoading(true);
    setError("");
    try {
      setRows(await api.listPayroll());
    } catch (err) {
      setError(toMessage(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  async function run(e: FormEvent): Promise<void> {
    e.preventDefault();
    setSaving(true);
    setError("");
    try {
      await api.runPayroll({
        staff_id: staffId,
        period,
        gross: Number(gross),
        allowances: allowances ? Number(allowances) : undefined,
        other_deductions: deductions ? Number(deductions) : undefined,
      });
      setStaffId("");
      setGross("");
      setAllowances("");
      setDeductions("");
      await refresh();
    } catch (err) {
      setError(toMessage(err));
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-5">
      <PageTitle>Payroll</PageTitle>
      <ErrorText>{error}</ErrorText>

      {canWrite && (
        <Card>
          <h2 className="mb-3 text-sm font-semibold text-slate-700">Run payslip</h2>
          <form onSubmit={run} className="grid grid-cols-1 gap-3 md:grid-cols-5">
            <Input
              placeholder="Staff ID"
              value={staffId}
              onChange={(e) => setStaffId(e.target.value)}
              required
            />
            <Input placeholder="Period (YYYY-MM)" value={period} onChange={(e) => setPeriod(e.target.value)} required />
            <Input
              type="number"
              placeholder="Gross"
              value={gross}
              onChange={(e) => setGross(e.target.value)}
              required
            />
            <Input
              type="number"
              placeholder="Allowances"
              value={allowances}
              onChange={(e) => setAllowances(e.target.value)}
            />
            <Input
              type="number"
              placeholder="Deductions"
              value={deductions}
              onChange={(e) => setDeductions(e.target.value)}
            />
            <div className="md:col-span-5">
              <Button type="submit" disabled={saving}>
                {saving ? "Computing..." : "Compute payslip"}
              </Button>
            </div>
          </form>
        </Card>
      )}

      <Card>
        <DataTable
          loading={loading}
          rows={rows}
          rowKey={(r) => r.id}
          empty="No payroll records yet."
          columns={[
            { header: "Staff", cell: (r) => r.staff_id.slice(0, 8) },
            { header: "Period", cell: (r) => r.period },
            { header: "Gross", cell: (r) => r.gross.toFixed(2) },
            { header: "PAYE", cell: (r) => r.paye.toFixed(2) },
            { header: "Net", cell: (r) => r.net.toFixed(2) },
            { header: "Status", cell: (r) => r.status },
          ]}
        />
      </Card>
    </div>
  );
}
