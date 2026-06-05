// Attendance: record a student's status for a date and view their attendance
// summary (rate + counts). Backed by /attendance.

import { useState, type FormEvent } from "react";
import * as api from "@/api/endpoints";
import type { AttendanceSummary } from "@/api/endpoints";
import { useAuthStore } from "@/store/authStore";
import { Button, Card, ErrorText, Input, PageTitle, Select, StatCard } from "@/components/ui";
import { toMessage } from "@/lib/errors";

const STATUSES = ["present", "absent", "late", "excused"];

export function AttendancePage(): JSX.Element {
  const can = useAuthStore((s) => s.can);
  const canWrite = can("attendance:write");

  const [studentId, setStudentId] = useState("");
  const [classId, setClassId] = useState("");
  const [onDate, setOnDate] = useState(new Date().toISOString().slice(0, 10));
  const [status, setStatus] = useState("present");
  const [summary, setSummary] = useState<AttendanceSummary | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function record(e: FormEvent): Promise<void> {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await api.markAttendance({
        student_id: studentId,
        class_id: classId,
        on_date: onDate,
        status,
      });
      setSummary(await api.attendanceSummary(studentId));
    } catch (err) {
      setError(toMessage(err));
    } finally {
      setBusy(false);
    }
  }

  async function lookup(): Promise<void> {
    if (!studentId) {
      return;
    }
    setError("");
    try {
      setSummary(await api.attendanceSummary(studentId));
    } catch (err) {
      setError(toMessage(err));
    }
  }

  return (
    <div className="space-y-5">
      <PageTitle>Attendance</PageTitle>
      <ErrorText>{error}</ErrorText>

      {canWrite && (
        <Card>
          <h2 className="mb-3 text-sm font-semibold text-slate-700">Record attendance</h2>
          <form onSubmit={record} className="grid grid-cols-1 gap-3 md:grid-cols-4">
            <Input
              placeholder="Student ID"
              value={studentId}
              onChange={(e) => setStudentId(e.target.value)}
              required
            />
            <Input
              placeholder="Class ID"
              value={classId}
              onChange={(e) => setClassId(e.target.value)}
              required
            />
            <Input type="date" value={onDate} onChange={(e) => setOnDate(e.target.value)} required />
            <Select value={status} onChange={(e) => setStatus(e.target.value)}>
              {STATUSES.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </Select>
            <div className="md:col-span-4">
              <Button type="submit" disabled={busy}>
                {busy ? "Saving..." : "Record"}
              </Button>
            </div>
          </form>
        </Card>
      )}

      <Card>
        <div className="mb-4 flex gap-2">
          <Input
            placeholder="Student ID to summarize"
            value={studentId}
            onChange={(e) => setStudentId(e.target.value)}
          />
          <Button onClick={lookup}>Summary</Button>
        </div>
        {summary && (
          <div className="grid grid-cols-2 gap-3 md:grid-cols-5">
            <StatCard label="Rate" value={`${Math.round(summary.rate * 100)}%`} />
            <StatCard label="Present" value={summary.present} />
            <StatCard label="Absent" value={summary.absent} />
            <StatCard label="Late" value={summary.late} />
            <StatCard label="Excused" value={summary.excused} />
          </div>
        )}
      </Card>
    </div>
  );
}
