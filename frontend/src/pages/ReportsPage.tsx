// Reports: finance summary, active student count, and exam ranking lookup.

import { useEffect, useState, type FormEvent } from "react";
import * as api from "@/api/endpoints";
import type { FinanceSummary, RankingEntry } from "@/api/endpoints";
import { Button, Card, DataTable, ErrorText, Input, PageTitle, StatCard } from "@/components/ui";
import { toMessage } from "@/lib/errors";

export function ReportsPage(): JSX.Element {
  const [finance, setFinance] = useState<FinanceSummary | null>(null);
  const [students, setStudents] = useState<number | null>(null);
  const [examId, setExamId] = useState("");
  const [ranking, setRanking] = useState<RankingEntry[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    (async () => {
      try {
        const [f, c] = await Promise.all([api.financeSummary(), api.studentCount()]);
        setFinance(f);
        setStudents(c.active_students);
      } catch (err) {
        setError(toMessage(err));
      }
    })();
  }, []);

  async function loadRanking(e: FormEvent): Promise<void> {
    e.preventDefault();
    setError("");
    try {
      setRanking(await api.examRanking(examId));
    } catch (err) {
      setError(toMessage(err));
    }
  }

  return (
    <div className="space-y-5">
      <PageTitle>Reports</PageTitle>
      <ErrorText>{error}</ErrorText>

      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <StatCard label="Active students" value={students ?? "-"} />
        <StatCard label="Total billed" value={finance ? finance.total_billed.toFixed(2) : "-"} />
        <StatCard label="Collected" value={finance ? finance.total_collected.toFixed(2) : "-"} />
        <StatCard
          label="Outstanding"
          value={finance ? finance.total_outstanding.toFixed(2) : "-"}
        />
      </div>

      <Card>
        <h2 className="mb-3 text-sm font-semibold text-slate-700">Exam ranking</h2>
        <form onSubmit={loadRanking} className="mb-4 flex gap-2">
          <Input placeholder="Examination ID" value={examId} onChange={(e) => setExamId(e.target.value)} />
          <Button type="submit">Rank</Button>
        </form>
        <DataTable
          rows={ranking}
          rowKey={(r) => r.student_id}
          empty="Enter an examination ID to see the ranking."
          columns={[
            { header: "Position", cell: (r) => r.position },
            { header: "Student", cell: (r) => r.student_id },
          ]}
        />
      </Card>
    </div>
  );
}
