// Communication hub: send a notification (in-app/SMS/email; degrades to in-app
// when no provider is configured) and view a recipient's inbox.

import { useState, type FormEvent } from "react";
import * as api from "@/api/endpoints";
import type { NotificationItem } from "@/api/endpoints";
import { useAuthStore } from "@/store/authStore";
import { Button, Card, DataTable, ErrorText, Input, PageTitle, Select } from "@/components/ui";
import { toMessage } from "@/lib/errors";

const CHANNELS = ["in_app", "sms", "email"];

export function CommunicationPage(): JSX.Element {
  const can = useAuthStore((s) => s.can);
  const canWrite = can("communication:write");

  const [recipientId, setRecipientId] = useState("");
  const [channel, setChannel] = useState("in_app");
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [notes, setNotes] = useState<NotificationItem[]>([]);
  const [info, setInfo] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function send(e: FormEvent): Promise<void> {
    e.preventDefault();
    setBusy(true);
    setError("");
    setInfo("");
    try {
      const res = await api.sendNotification({
        recipient_id: recipientId,
        channel,
        subject: subject || undefined,
        body,
      });
      setInfo(
        res.delivered_externally
          ? `Sent via ${res.channel}.`
          : `Queued in-app (no ${channel} provider configured).`,
      );
      setBody("");
      setSubject("");
      await loadInbox();
    } catch (err) {
      setError(toMessage(err));
    } finally {
      setBusy(false);
    }
  }

  async function loadInbox(): Promise<void> {
    if (!recipientId) {
      return;
    }
    setError("");
    try {
      setNotes(await api.listNotifications(recipientId));
    } catch (err) {
      setError(toMessage(err));
    }
  }

  return (
    <div className="space-y-5">
      <PageTitle>Communication</PageTitle>
      <ErrorText>{error}</ErrorText>
      {info && <p className="text-sm text-emerald-700">{info}</p>}

      {canWrite && (
        <Card>
          <h2 className="mb-3 text-sm font-semibold text-slate-700">Send notification</h2>
          <form onSubmit={send} className="space-y-3">
            <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
              <Input
                placeholder="Recipient ID"
                value={recipientId}
                onChange={(e) => setRecipientId(e.target.value)}
                required
              />
              <Select value={channel} onChange={(e) => setChannel(e.target.value)}>
                {CHANNELS.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </Select>
              <Input placeholder="Subject" value={subject} onChange={(e) => setSubject(e.target.value)} />
            </div>
            <Input placeholder="Message" value={body} onChange={(e) => setBody(e.target.value)} required />
            <Button type="submit" disabled={busy}>
              {busy ? "Sending..." : "Send"}
            </Button>
          </form>
        </Card>
      )}

      <Card>
        <div className="mb-4 flex gap-2">
          <Input
            placeholder="Recipient ID to view inbox"
            value={recipientId}
            onChange={(e) => setRecipientId(e.target.value)}
          />
          <Button onClick={loadInbox}>Load inbox</Button>
        </div>
        <DataTable
          rows={notes}
          rowKey={(r) => r.id}
          empty="No notifications."
          columns={[
            { header: "Channel", cell: (r) => r.channel },
            { header: "Subject", cell: (r) => r.subject ?? "-" },
            { header: "Message", cell: (r) => r.body },
            { header: "Read", cell: (r) => (r.read ? "yes" : "no") },
          ]}
        />
      </Card>
    </div>
  );
}
