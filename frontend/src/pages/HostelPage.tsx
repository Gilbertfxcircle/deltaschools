// Hostel: rooms + capacity-checked allocations.

import { useEffect, useState, type FormEvent } from "react";
import * as api from "@/api/endpoints";
import type { AllocationItem, RoomItem } from "@/api/endpoints";
import { useAuthStore } from "@/store/authStore";
import { Button, Card, DataTable, ErrorText, Input, PageTitle } from "@/components/ui";
import { toMessage } from "@/lib/errors";

export function HostelPage(): JSX.Element {
  const can = useAuthStore((s) => s.can);
  const canWrite = can("hostel:write");

  const [rooms, setRooms] = useState<RoomItem[]>([]);
  const [allocations, setAllocations] = useState<AllocationItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [roomName, setRoomName] = useState("");
  const [capacity, setCapacity] = useState("1");
  const [roomId, setRoomId] = useState("");
  const [studentId, setStudentId] = useState("");
  const [year, setYear] = useState(String(new Date().getFullYear()));

  async function refresh(): Promise<void> {
    setLoading(true);
    setError("");
    try {
      const [r, a] = await Promise.all([api.listRooms(), api.listAllocations()]);
      setRooms(r);
      setAllocations(a);
    } catch (err) {
      setError(toMessage(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  async function addRoom(e: FormEvent): Promise<void> {
    e.preventDefault();
    setError("");
    try {
      await api.createRoom({ name: roomName, capacity: Number(capacity) });
      setRoomName("");
      setCapacity("1");
      await refresh();
    } catch (err) {
      setError(toMessage(err));
    }
  }

  async function allocate(e: FormEvent): Promise<void> {
    e.preventDefault();
    setError("");
    try {
      await api.allocateRoom({ room_id: roomId, student_id: studentId, academic_year: year });
      setRoomId("");
      setStudentId("");
      await refresh();
    } catch (err) {
      setError(toMessage(err));
    }
  }

  return (
    <div className="space-y-5">
      <PageTitle>Hostel</PageTitle>
      <ErrorText>{error}</ErrorText>

      {canWrite && (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <Card>
            <h2 className="mb-3 text-sm font-semibold text-slate-700">Add room</h2>
            <form onSubmit={addRoom} className="space-y-3">
              <Input placeholder="Room name" value={roomName} onChange={(e) => setRoomName(e.target.value)} required />
              <Input
                type="number"
                placeholder="Capacity"
                value={capacity}
                onChange={(e) => setCapacity(e.target.value)}
              />
              <Button type="submit">Add room</Button>
            </form>
          </Card>
          <Card>
            <h2 className="mb-3 text-sm font-semibold text-slate-700">Allocate</h2>
            <form onSubmit={allocate} className="space-y-3">
              <Input placeholder="Room ID" value={roomId} onChange={(e) => setRoomId(e.target.value)} required />
              <Input
                placeholder="Student ID"
                value={studentId}
                onChange={(e) => setStudentId(e.target.value)}
                required
              />
              <Input placeholder="Academic year" value={year} onChange={(e) => setYear(e.target.value)} />
              <Button type="submit">Allocate</Button>
            </form>
          </Card>
        </div>
      )}

      <Card>
        <h2 className="mb-3 text-sm font-semibold text-slate-700">Rooms</h2>
        <DataTable
          loading={loading}
          rows={rooms}
          rowKey={(r) => r.id}
          empty="No rooms yet."
          columns={[
            { header: "Name", cell: (r) => r.name },
            { header: "Capacity", cell: (r) => r.capacity },
            { header: "ID", cell: (r) => r.id.slice(0, 8) },
          ]}
        />
      </Card>

      <Card>
        <h2 className="mb-3 text-sm font-semibold text-slate-700">Allocations</h2>
        <DataTable
          loading={loading}
          rows={allocations}
          rowKey={(r) => r.id}
          empty="No allocations yet."
          columns={[
            { header: "Room", cell: (r) => r.room_id.slice(0, 8) },
            { header: "Student", cell: (r) => r.student_id.slice(0, 8) },
            { header: "Year", cell: (r) => r.academic_year },
          ]}
        />
      </Card>
    </div>
  );
}
