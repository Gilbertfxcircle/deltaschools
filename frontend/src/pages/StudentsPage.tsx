// Students list + create. Create is only offered to users with students:write
// (the server enforces it regardless). National ID is sent for encryption at
// rest on the backend; it is never displayed here.

import { useEffect, useState, type FormEvent } from "react";
import * as api from "@/api/endpoints";
import type { Student } from "@/api/types";
import { useAuthStore } from "@/store/authStore";
import { Button, Card, ErrorText, Input, PageTitle } from "@/components/ui";
import { toMessage } from "@/lib/errors";

export function StudentsPage(): JSX.Element {
  const can = useAuthStore((s) => s.can);
  const canWrite = can("students:write");

  const [students, setStudents] = useState<Student[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const [admissionNo, setAdmissionNo] = useState("");
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [nationalId, setNationalId] = useState("");
  const [saving, setSaving] = useState(false);

  async function refresh(): Promise<void> {
    setLoading(true);
    setError("");
    try {
      setStudents(await api.listStudents());
    } catch (err) {
      setError(toMessage(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  async function onCreate(e: FormEvent): Promise<void> {
    e.preventDefault();
    setSaving(true);
    setError("");
    try {
      await api.createStudent({
        admission_no: admissionNo,
        first_name: firstName,
        last_name: lastName,
        national_id: nationalId || undefined,
      });
      setAdmissionNo("");
      setFirstName("");
      setLastName("");
      setNationalId("");
      await refresh();
    } catch (err) {
      setError(toMessage(err));
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-5">
      <PageTitle>Students</PageTitle>
      <ErrorText>{error}</ErrorText>

      {canWrite && (
        <Card>
          <h2 className="mb-3 text-sm font-semibold text-slate-700">Add student</h2>
          <form onSubmit={onCreate} className="grid grid-cols-1 gap-3 md:grid-cols-4">
            <Input
              placeholder="Admission no."
              value={admissionNo}
              onChange={(e) => setAdmissionNo(e.target.value)}
              required
            />
            <Input
              placeholder="First name"
              value={firstName}
              onChange={(e) => setFirstName(e.target.value)}
              required
            />
            <Input
              placeholder="Last name"
              value={lastName}
              onChange={(e) => setLastName(e.target.value)}
              required
            />
            <Input
              placeholder="National ID (optional)"
              value={nationalId}
              onChange={(e) => setNationalId(e.target.value)}
            />
            <div className="md:col-span-4">
              <Button type="submit" disabled={saving}>
                {saving ? "Saving..." : "Create student"}
              </Button>
            </div>
          </form>
        </Card>
      )}

      <Card>
        {loading ? (
          <p className="text-sm text-slate-500">Loading...</p>
        ) : students.length === 0 ? (
          <p className="text-sm text-slate-500">No students yet.</p>
        ) : (
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-slate-500">
                <th className="py-2">Admission no.</th>
                <th className="py-2">Name</th>
                <th className="py-2">Gender</th>
              </tr>
            </thead>
            <tbody>
              {students.map((s) => (
                <tr key={s.id} className="border-b border-slate-100">
                  <td className="py-2">{s.admission_no}</td>
                  <td className="py-2">{s.name}</td>
                  <td className="py-2">{s.gender ?? "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>
    </div>
  );
}
