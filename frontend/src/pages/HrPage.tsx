// Staff & HR: manage staff records and leave requests (approve/reject).

import { useEffect, useState, type FormEvent } from "react";
import * as api from "@/api/endpoints";
import type { LeaveItem, StaffItem } from "@/api/endpoints";
import { useAuthStore } from "@/store/authStore";
import { Button, Card, DataTable, ErrorText, Input, PageTitle } from "@/components/ui";
import { toMessage } from "@/lib/errors";

export function HrPage(): JSX.Element {
  const can = useAuthStore((s) => s.can);
  const canWrite = can("staff:write");

  const [staff, setStaff] = useState<StaffItem[]>([]);
  const [leaves, setLeaves] = useState<LeaveItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [staffNo, setStaffNo] = useState("");
  const [fullName, setFullName] = useState("");
  const [designation, setDesignation] = useState("");
  const [saving, setSaving] = useState(false);

  async function refresh(): Promise<void> {
    setLoading(true);
    setError("");
    try {
      const [s, l] = await Promise.all([api.listStaff(), api.listLeaves()]);
      setStaff(s);
      setLeaves(l);
    } catch (err) {
      setError(toMessage(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  async function addStaff(e: FormEvent): Promise<void> {
    e.preventDefault();
    setSaving(true);
    setError("");
    try {
      await api.createStaff({
        staff_no: staffNo,
        full_name: fullName,
        designation: designation || undefined,
      });
      setStaffNo("");
      setFullName("");
      setDesignation("");
      await refresh();
    } catch (err) {
      setError(toMessage(err));
    } finally {
      setSaving(false);
    }
  }

  async function decide(id: string, decision: "approved" | "rejected"): Promise<void> {
    setError("");
    try {
      await api.decideLeave(id, decision);
      await refresh();
    } catch (err) {
      setError(toMessage(err));
    }
  }

  return (
    <div className="space-y-5">
      <PageTitle>Staff &amp; HR</PageTitle>
      <ErrorText>{error}</ErrorText>

      {canWrite && (
        <Card>
          <h2 className="mb-3 text-sm font-semibold text-slate-700">Add staff</h2>
          <form onSubmit={addStaff} className="grid grid-cols-1 gap-3 md:grid-cols-4">
            <Input placeholder="Staff no." value={staffNo} onChange={(e) => setStaffNo(e.target.value)} required />
            <Input placeholder="Full name" value={fullName} onChange={(e) => setFullName(e.target.value)} required />
            <Input
              placeholder="Designation"
              value={designation}
              onChange={(e) => setDesignation(e.target.value)}
            />
            <div className="md:col-span-4">
              <Button type="submit" disabled={saving}>
                {saving ? "Saving..." : "Add staff"}
              </Button>
            </div>
          </form>
        </Card>
      )}

      <Card>
        <h2 className="mb-3 text-sm font-semibold text-slate-700">Staff</h2>
        <DataTable
          loading={loading}
          rows={staff}
          rowKey={(r) => r.id}
          empty="No staff yet."
          columns={[
            { header: "Staff no.", cell: (r) => r.staff_no },
            { header: "Name", cell: (r) => r.name },
            { header: "Designation", cell: (r) => r.designation ?? "-" },
          ]}
        />
      </Card>

      <Card>
        <h2 className="mb-3 text-sm font-semibold text-slate-700">Leave requests</h2>
        <DataTable
          loading={loading}
          rows={leaves}
          rowKey={(r) => r.id}
          empty="No leave requests."
          columns={[
            { header: "Staff", cell: (r) => r.staff_id.slice(0, 8) },
            { header: "Type", cell: (r) => r.leave_type },
            { header: "From", cell: (r) => r.start_date ?? "-" },
            { header: "To", cell: (r) => r.end_date ?? "-" },
            { header: "Status", cell: (r) => r.status },
            {
              header: "Action",
              cell: (r) =>
                canWrite && r.status === "pending" ? (
                  <span className="inline-flex gap-2">
                    <Button onClick={() => decide(r.id, "approved")}>Approve</Button>
                    <button
                      onClick={() => decide(r.id, "rejected")}
                      className="rounded px-3 py-1 text-sm font-medium text-white"
                      style={{ background: "#b91c1c" }}
                    >
                      Reject
                    </button>
                  </span>
                ) : (
                  <span className="text-slate-400">&mdash;</span>
                ),
            },
          ]}
        />
      </Card>
    </div>
  );
}
