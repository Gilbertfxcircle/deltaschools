// Library: catalog management, loan a book, and return loans. Availability is
// tracked server-side.

import { useEffect, useState, type FormEvent } from "react";
import * as api from "@/api/endpoints";
import type { BookItem, LoanItem } from "@/api/endpoints";
import { useAuthStore } from "@/store/authStore";
import { Button, Card, DataTable, ErrorText, Input, PageTitle } from "@/components/ui";
import { toMessage } from "@/lib/errors";

export function LibraryPage(): JSX.Element {
  const can = useAuthStore((s) => s.can);
  const canWrite = can("library:write");

  const [books, setBooks] = useState<BookItem[]>([]);
  const [loans, setLoans] = useState<LoanItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [title, setTitle] = useState("");
  const [author, setAuthor] = useState("");
  const [copies, setCopies] = useState("1");
  const [borrowerId, setBorrowerId] = useState("");
  const [bookId, setBookId] = useState("");

  async function refresh(): Promise<void> {
    setLoading(true);
    setError("");
    try {
      const [b, l] = await Promise.all([api.listBooks(), api.listLoans()]);
      setBooks(b);
      setLoans(l);
    } catch (err) {
      setError(toMessage(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  async function addBook(e: FormEvent): Promise<void> {
    e.preventDefault();
    setError("");
    try {
      await api.addBook({ title, author: author || undefined, total_copies: Number(copies) });
      setTitle("");
      setAuthor("");
      setCopies("1");
      await refresh();
    } catch (err) {
      setError(toMessage(err));
    }
  }

  async function loan(e: FormEvent): Promise<void> {
    e.preventDefault();
    setError("");
    try {
      await api.loanBook({ book_id: bookId, borrower_id: borrowerId });
      setBookId("");
      setBorrowerId("");
      await refresh();
    } catch (err) {
      setError(toMessage(err));
    }
  }

  async function ret(loanId: string): Promise<void> {
    setError("");
    try {
      await api.returnBook(loanId);
      await refresh();
    } catch (err) {
      setError(toMessage(err));
    }
  }

  return (
    <div className="space-y-5">
      <PageTitle>Library</PageTitle>
      <ErrorText>{error}</ErrorText>

      {canWrite && (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <Card>
            <h2 className="mb-3 text-sm font-semibold text-slate-700">Add book</h2>
            <form onSubmit={addBook} className="space-y-3">
              <Input placeholder="Title" value={title} onChange={(e) => setTitle(e.target.value)} required />
              <Input placeholder="Author" value={author} onChange={(e) => setAuthor(e.target.value)} />
              <Input type="number" placeholder="Copies" value={copies} onChange={(e) => setCopies(e.target.value)} />
              <Button type="submit">Add book</Button>
            </form>
          </Card>
          <Card>
            <h2 className="mb-3 text-sm font-semibold text-slate-700">Loan a book</h2>
            <form onSubmit={loan} className="space-y-3">
              <Input placeholder="Book ID" value={bookId} onChange={(e) => setBookId(e.target.value)} required />
              <Input
                placeholder="Borrower ID"
                value={borrowerId}
                onChange={(e) => setBorrowerId(e.target.value)}
                required
              />
              <Button type="submit">Loan</Button>
            </form>
          </Card>
        </div>
      )}

      <Card>
        <h2 className="mb-3 text-sm font-semibold text-slate-700">Catalog</h2>
        <DataTable
          loading={loading}
          rows={books}
          rowKey={(r) => r.id}
          empty="No books in the catalog."
          columns={[
            { header: "Title", cell: (r) => r.title },
            { header: "Author", cell: (r) => r.author ?? "-" },
            { header: "Available", cell: (r) => `${r.available} / ${r.total}` },
            { header: "ID", cell: (r) => r.id.slice(0, 8) },
          ]}
        />
      </Card>

      <Card>
        <h2 className="mb-3 text-sm font-semibold text-slate-700">Loans</h2>
        <DataTable
          loading={loading}
          rows={loans}
          rowKey={(r) => r.id}
          empty="No active loans."
          columns={[
            { header: "Book", cell: (r) => r.book_id.slice(0, 8) },
            { header: "Borrower", cell: (r) => r.borrower_id.slice(0, 8) },
            { header: "Due", cell: (r) => (r.due_at ? r.due_at.slice(0, 10) : "-") },
            {
              header: "Status",
              cell: (r) => (r.returned_at ? "returned" : "out"),
            },
            {
              header: "Action",
              cell: (r) =>
                canWrite && !r.returned_at ? (
                  <Button onClick={() => ret(r.id)}>Return</Button>
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
