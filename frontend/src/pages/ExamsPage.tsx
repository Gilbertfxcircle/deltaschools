// Exams: create examinations, record marks (grade derived server-side), and
// generate a report card from a student's marks for an exam.

import { useEffect, useState, type FormEvent } from "react";
import * as api from "@/api/endpoints";
import type { ExamItem, ReportCardResult } from "@/api/endpoints";
import { useAuthStore } from "@/store/authStore";
import { Button, Card, DataTable, ErrorText, Input, PageTitle } from "@/components/ui";
import { toMessage } from "@/lib/errors";

export function ExamsPage(): JSX.Element {
  const can = useAuthStore((s) => s.can);
  const canWriteExam = can("exams:write");
  const canWriteMark = can("marks:write");

  const [exams, setExams] = useState<ExamItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [name, setName] = useState("");
  const [year, setYear] = useState(String(new Date().getFullYear()));
  const [term, setTerm] = useState("");

  const [examId, setExamId] = useState("");
  const [studentId, setStudentId] = useState("");
  const [subjectId, setSubjectId] = useState("");
  const [score, setScore] = useState("");

  const [reportCard, setReportCard] = useState<ReportCardResult | null>(null);

  async function refresh(): Promise<void> {
    setLoading(true);
    setError("");
    try {
      setExams(await api.listExams());
    } catch (err) {
      setError(toMessage(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  async function createExam(e: FormEvent): Promise<void> {
    e.preventDefault();
    setError("");
    try {
      await api.createExam({ name, academic_year: year, term: term || undefined });
      setName("");
      setTerm("");
      await refresh();
    } catch (err) {
      setError(toMessage(err));
    }
  }

  async function recordMark(e: FormEvent): Promise<void> {
    e.preventDefault();
    setError("");
    try {
      await api.recordMark({
        examination_id: examId,
        student_id: studentId,
        subject_id: subjectId,
        score: Number(score),
      });
      setScore("");
    } catch (err) {
      setError(toMessage(err));
    }
  }

  async function genReport(): Promise<void> {
    setError("");
    setReportCard(null);
    try {
      setReportCard(await api.generateReportCard(examId, studentId));
    } catch (err) {
      setError(toMessage(err));
    }
  }

  return (
    <div className="space-y-5">
      <PageTitle>Examinations</PageTitle>
      <ErrorText>{error}</ErrorText>

      {canWriteExam && (
        <Card>
          <h2 className="mb-3 text-sm font-semibold text-slate-700">Create examination</h2>
          <form onSubmit={createExam} className="grid grid-cols-1 gap-3 md:grid-cols-4">
            <Input placeholder="Name" value={name} onChange={(e) => setName(e.target.value)} required />
            <Input placeholder="Academic year" value={year} onChange={(e) => setYear(e.target.value)} required />
            <Input placeholder="Term" value={term} onChange={(e) => setTerm(e.target.value)} />
            <Button type="submit">Create</Button>
          </form>
        </Card>
      )}

      <Card>
        <h2 className="mb-3 text-sm font-semibold text-slate-700">Examinations</h2>
        <DataTable
          loading={loading}
          rows={exams}
          rowKey={(r) => r.id}
          empty="No examinations yet."
          columns={[
            { header: "Name", cell: (r) => r.name },
            { header: "Year", cell: (r) => r.academic_year },
            { header: "Term", cell: (r) => r.term ?? "-" },
            { header: "ID", cell: (r) => r.id.slice(0, 8) },
          ]}
        />
      </Card>

      {canWriteMark && (
        <Card>
          <h2 className="mb-3 text-sm font-semibold text-slate-700">Record mark</h2>
          <form onSubmit={recordMark} className="grid grid-cols-1 gap-3 md:grid-cols-5">
            <Input placeholder="Exam ID" value={examId} onChange={(e) => setExamId(e.target.value)} required />
            <Input
              placeholder="Student ID"
              value={studentId}
              onChange={(e) => setStudentId(e.target.value)}
              required
            />
            <Input
              placeholder="Subject ID"
              value={subjectId}
              onChange={(e) => setSubjectId(e.target.value)}
              required
            />
            <Input
              type="number"
              placeholder="Score"
              value={score}
              onChange={(e) => setScore(e.target.value)}
              required
            />
            <Button type="submit">Record</Button>
          </form>
        </Card>
      )}

      <Card>
        <h2 className="mb-3 text-sm font-semibold text-slate-700">Generate report card</h2>
        <div className="mb-4 flex flex-wrap gap-2">
          <Input placeholder="Exam ID" value={examId} onChange={(e) => setExamId(e.target.value)} />
          <Input placeholder="Student ID" value={studentId} onChange={(e) => setStudentId(e.target.value)} />
          <Button onClick={genReport}>Generate</Button>
        </div>
        {reportCard && (
          <div className="space-y-3">
            <div className="flex gap-6 text-sm">
              <span>Average: <strong>{reportCard.average}</strong></span>
              <span>GPA: <strong>{reportCard.gpa}</strong></span>
              <span>Grade: <strong>{reportCard.overall_grade}</strong></span>
            </div>
            <DataTable
              rows={reportCard.subjects}
              rowKey={(r) => r.subject}
              columns={[
                { header: "Subject", cell: (r) => r.subject },
                { header: "Score", cell: (r) => r.score },
              ]}
            />
          </div>
        )}
      </Card>
    </div>
  );
}
