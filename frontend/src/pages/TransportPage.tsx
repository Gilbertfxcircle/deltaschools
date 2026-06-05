// Transport: routes + student assignments.

import { useEffect, useState, type FormEvent } from "react";
import * as api from "@/api/endpoints";
import type { AssignmentItem, RouteItem } from "@/api/endpoints";
import { useAuthStore } from "@/store/authStore";
import { Button, Card, DataTable, ErrorText, Input, PageTitle } from "@/components/ui";
import { toMessage } from "@/lib/errors";

export function TransportPage(): JSX.Element {
  const can = useAuthStore((s) => s.can);
  const canWrite = can("transport:write");

  const [routes, setRoutes] = useState<RouteItem[]>([]);
  const [assignments, setAssignments] = useState<AssignmentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [routeName, setRouteName] = useState("");
  const [fee, setFee] = useState("0");
  const [routeId, setRouteId] = useState("");
  const [studentId, setStudentId] = useState("");
  const [stop, setStop] = useState("");

  async function refresh(): Promise<void> {
    setLoading(true);
    setError("");
    try {
      const [r, a] = await Promise.all([api.listRoutes(), api.listAssignments()]);
      setRoutes(r);
      setAssignments(a);
    } catch (err) {
      setError(toMessage(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  async function addRoute(e: FormEvent): Promise<void> {
    e.preventDefault();
    setError("");
    try {
      await api.createRoute({ name: routeName, fee: Number(fee) });
      setRouteName("");
      setFee("0");
      await refresh();
    } catch (err) {
      setError(toMessage(err));
    }
  }

  async function assign(e: FormEvent): Promise<void> {
    e.preventDefault();
    setError("");
    try {
      await api.assignTransport({ route_id: routeId, student_id: studentId, stop_name: stop || undefined });
      setRouteId("");
      setStudentId("");
      setStop("");
      await refresh();
    } catch (err) {
      setError(toMessage(err));
    }
  }

  return (
    <div className="space-y-5">
      <PageTitle>Transport</PageTitle>
      <ErrorText>{error}</ErrorText>

      {canWrite && (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <Card>
            <h2 className="mb-3 text-sm font-semibold text-slate-700">Add route</h2>
            <form onSubmit={addRoute} className="space-y-3">
              <Input placeholder="Route name" value={routeName} onChange={(e) => setRouteName(e.target.value)} required />
              <Input type="number" placeholder="Fee" value={fee} onChange={(e) => setFee(e.target.value)} />
              <Button type="submit">Add route</Button>
            </form>
          </Card>
          <Card>
            <h2 className="mb-3 text-sm font-semibold text-slate-700">Assign student</h2>
            <form onSubmit={assign} className="space-y-3">
              <Input placeholder="Route ID" value={routeId} onChange={(e) => setRouteId(e.target.value)} required />
              <Input
                placeholder="Student ID"
                value={studentId}
                onChange={(e) => setStudentId(e.target.value)}
                required
              />
              <Input placeholder="Stop name" value={stop} onChange={(e) => setStop(e.target.value)} />
              <Button type="submit">Assign</Button>
            </form>
          </Card>
        </div>
      )}

      <Card>
        <h2 className="mb-3 text-sm font-semibold text-slate-700">Routes</h2>
        <DataTable
          loading={loading}
          rows={routes}
          rowKey={(r) => r.id}
          empty="No routes yet."
          columns={[
            { header: "Name", cell: (r) => r.name },
            { header: "Fee", cell: (r) => r.fee.toFixed(2) },
            { header: "ID", cell: (r) => r.id.slice(0, 8) },
          ]}
        />
      </Card>

      <Card>
        <h2 className="mb-3 text-sm font-semibold text-slate-700">Assignments</h2>
        <DataTable
          loading={loading}
          rows={assignments}
          rowKey={(r) => r.id}
          empty="No assignments yet."
          columns={[
            { header: "Route", cell: (r) => r.route_id.slice(0, 8) },
            { header: "Student", cell: (r) => r.student_id.slice(0, 8) },
            { header: "Stop", cell: (r) => r.stop_name ?? "-" },
          ]}
        />
      </Card>
    </div>
  );
}
