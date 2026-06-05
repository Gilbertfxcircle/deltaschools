// Document management: register document metadata (binary upload goes to MinIO
// separately). The backend rejects extension/MIME mismatches.

import { useEffect, useState, type FormEvent } from "react";
import * as api from "@/api/endpoints";
import type { DocumentItem } from "@/api/endpoints";
import { useAuthStore } from "@/store/authStore";
import { Button, Card, DataTable, ErrorText, Input, PageTitle } from "@/components/ui";
import { toMessage } from "@/lib/errors";

export function DocumentsPage(): JSX.Element {
  const can = useAuthStore((s) => s.can);
  const canWrite = can("documents:write");

  const [docs, setDocs] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [name, setName] = useState("");
  const [storageKey, setStorageKey] = useState("");
  const [contentType, setContentType] = useState("application/pdf");

  async function refresh(): Promise<void> {
    setLoading(true);
    setError("");
    try {
      setDocs(await api.listDocuments());
    } catch (err) {
      setError(toMessage(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  async function register(e: FormEvent): Promise<void> {
    e.preventDefault();
    setError("");
    try {
      await api.registerDocument({ name, storage_key: storageKey, content_type: contentType });
      setName("");
      setStorageKey("");
      await refresh();
    } catch (err) {
      setError(toMessage(err));
    }
  }

  return (
    <div className="space-y-5">
      <PageTitle>Documents</PageTitle>
      <ErrorText>{error}</ErrorText>

      {canWrite && (
        <Card>
          <h2 className="mb-3 text-sm font-semibold text-slate-700">Register document</h2>
          <form onSubmit={register} className="grid grid-cols-1 gap-3 md:grid-cols-3">
            <Input placeholder="File name (e.g. report.pdf)" value={name} onChange={(e) => setName(e.target.value)} required />
            <Input
              placeholder="Storage key"
              value={storageKey}
              onChange={(e) => setStorageKey(e.target.value)}
              required
            />
            <Input
              placeholder="Content type"
              value={contentType}
              onChange={(e) => setContentType(e.target.value)}
            />
            <div className="md:col-span-3">
              <Button type="submit">Register</Button>
            </div>
          </form>
        </Card>
      )}

      <Card>
        <DataTable
          loading={loading}
          rows={docs}
          rowKey={(r) => r.id}
          empty="No documents registered."
          columns={[
            { header: "Name", cell: (r) => r.name },
            { header: "Type", cell: (r) => r.content_type ?? "-" },
            { header: "Size", cell: (r) => (r.size != null ? `${r.size} B` : "-") },
          ]}
        />
      </Card>
    </div>
  );
}
