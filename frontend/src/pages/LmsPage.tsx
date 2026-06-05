// E-Learning: courses and their lessons. Selecting a course loads its lessons.

import { useEffect, useState, type FormEvent } from "react";
import * as api from "@/api/endpoints";
import type { CourseItem, LessonItem } from "@/api/endpoints";
import { useAuthStore } from "@/store/authStore";
import { Button, Card, DataTable, ErrorText, Input, PageTitle } from "@/components/ui";
import { toMessage } from "@/lib/errors";

export function LmsPage(): JSX.Element {
  const can = useAuthStore((s) => s.can);
  const canWrite = can("lms:write");

  const [courses, setCourses] = useState<CourseItem[]>([]);
  const [lessons, setLessons] = useState<LessonItem[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [lessonTitle, setLessonTitle] = useState("");

  async function refresh(): Promise<void> {
    setLoading(true);
    setError("");
    try {
      setCourses(await api.listCourses());
    } catch (err) {
      setError(toMessage(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  async function selectCourse(courseId: string): Promise<void> {
    setSelected(courseId);
    setError("");
    try {
      setLessons(await api.listLessons(courseId));
    } catch (err) {
      setError(toMessage(err));
    }
  }

  async function addCourse(e: FormEvent): Promise<void> {
    e.preventDefault();
    setError("");
    try {
      await api.createCourse({ title, description: description || undefined });
      setTitle("");
      setDescription("");
      await refresh();
    } catch (err) {
      setError(toMessage(err));
    }
  }

  async function addLesson(e: FormEvent): Promise<void> {
    e.preventDefault();
    if (!selected) {
      return;
    }
    setError("");
    try {
      await api.createLesson({ course_id: selected, title: lessonTitle, position: lessons.length });
      setLessonTitle("");
      await selectCourse(selected);
    } catch (err) {
      setError(toMessage(err));
    }
  }

  return (
    <div className="space-y-5">
      <PageTitle>E-Learning</PageTitle>
      <ErrorText>{error}</ErrorText>

      {canWrite && (
        <Card>
          <h2 className="mb-3 text-sm font-semibold text-slate-700">Create course</h2>
          <form onSubmit={addCourse} className="grid grid-cols-1 gap-3 md:grid-cols-3">
            <Input placeholder="Title" value={title} onChange={(e) => setTitle(e.target.value)} required />
            <Input
              placeholder="Description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
            <Button type="submit">Create course</Button>
          </form>
        </Card>
      )}

      <Card>
        <h2 className="mb-3 text-sm font-semibold text-slate-700">Courses</h2>
        <DataTable
          loading={loading}
          rows={courses}
          rowKey={(r) => r.id}
          empty="No courses yet."
          columns={[
            { header: "Title", cell: (r) => r.title },
            { header: "Description", cell: (r) => r.description ?? "-" },
            {
              header: "",
              cell: (r) => <Button onClick={() => selectCourse(r.id)}>View lessons</Button>,
            },
          ]}
        />
      </Card>

      {selected && (
        <Card>
          <h2 className="mb-3 text-sm font-semibold text-slate-700">Lessons</h2>
          {canWrite && (
            <form onSubmit={addLesson} className="mb-4 flex gap-2">
              <Input
                placeholder="Lesson title"
                value={lessonTitle}
                onChange={(e) => setLessonTitle(e.target.value)}
                required
              />
              <Button type="submit">Add lesson</Button>
            </form>
          )}
          <DataTable
            rows={lessons}
            rowKey={(r) => r.id}
            empty="No lessons in this course."
            columns={[
              { header: "#", cell: (r) => r.position + 1 },
              { header: "Title", cell: (r) => r.title },
              {
                header: "Resource",
                cell: (r) => (r.content_url ? r.content_url : "-"),
              },
            ]}
          />
        </Card>
      )}
    </div>
  );
}
