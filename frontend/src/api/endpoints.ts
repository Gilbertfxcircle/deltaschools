// Typed wrappers around the backend's /api/v1 endpoints. Each function returns
// already-unwrapped data (or throws ApiError).

import { apiGet, apiPatch, apiPost } from "@/api/client";
import type {
  ApprovalRequestSummary,
  AuditEntry,
  Branding,
  ModuleKey,
  Student,
  TokenPair,
} from "@/api/types";

// --- Auth ---
export interface LoginPayload {
  email: string;
  password: string;
  totp_code?: string;
}

export function login(payload: LoginPayload): Promise<TokenPair> {
  return apiPost<TokenPair>("/auth/login", payload);
}

export function logout(): Promise<unknown> {
  return apiPost<unknown>("/auth/logout");
}

// --- Modules (drives navigation) ---
export function getEnabledModules(): Promise<ModuleKey[]> {
  return apiGet<ModuleKey[]>("/modules/enabled");
}

export function getAvailableModules(): Promise<ModuleKey[]> {
  return apiGet<ModuleKey[]>("/modules/available");
}

// --- Branding (per-tenant) ---
export async function getBranding(): Promise<Branding> {
  const data = await apiGet<{ branding: Branding }>("/institutions/branding");
  return data.branding ?? {};
}

// --- Students ---
export function listStudents(): Promise<Student[]> {
  return apiGet<Student[]>("/students");
}

export interface CreateStudentPayload {
  admission_no: string;
  first_name: string;
  last_name: string;
  gender?: string;
  national_id?: string;
}

export function createStudent(payload: CreateStudentPayload): Promise<{ id: string }> {
  return apiPost<{ id: string }>("/students", payload);
}

// --- Approvals ---
export function listApprovals(): Promise<ApprovalRequestSummary[]> {
  return apiGet<ApprovalRequestSummary[]>("/approvals");
}

export function decideApproval(
  id: string,
  decision: "approved" | "rejected",
  notes?: string,
): Promise<{ id: string; state: string }> {
  return apiPatch<{ id: string; state: string }>(`/approvals/${id}`, { decision, notes });
}

// --- Audit (read-only) ---
export function listAudit(limit = 100): Promise<AuditEntry[]> {
  return apiGet<AuditEntry[]>("/audit", { params: { limit } });
}

// --- Finance (billing module) ---
export interface InvoiceSummary {
  id: string;
  amount: number;
  balance: number;
  status: string;
}

export function studentInvoices(studentId: string): Promise<InvoiceSummary[]> {
  return apiGet<InvoiceSummary[]>(`/finance/invoices/student/${studentId}`);
}

export interface CreateInvoicePayload {
  student_id: string;
  fee_structure_id: string;
  amount: number;
}

export function createInvoice(
  payload: CreateInvoicePayload,
): Promise<{ id: string; balance: number }> {
  return apiPost<{ id: string; balance: number }>("/finance/invoices", payload);
}

export interface RecordPaymentPayload {
  invoice_id: string;
  student_id: string;
  amount: number;
  method?: string;
  reference?: string;
}

export function recordPayment(
  payload: RecordPaymentPayload,
): Promise<{ payment_id: string; balance: number; status: string }> {
  return apiPost<{ payment_id: string; balance: number; status: string }>(
    "/finance/payments",
    payload,
  );
}

export interface FinanceSummary {
  total_billed: number;
  total_outstanding: number;
  total_collected: number;
}

export function financeSummary(): Promise<FinanceSummary> {
  return apiGet<FinanceSummary>("/reports/finance/summary");
}

// --- Attendance ---
export interface AttendanceSummary {
  student_id: string;
  total: number;
  present: number;
  absent: number;
  late: number;
  excused: number;
  rate: number;
}

export function attendanceSummary(studentId: string): Promise<AttendanceSummary> {
  return apiGet<AttendanceSummary>(`/attendance/student/${studentId}/summary`);
}

export interface MarkAttendancePayload {
  student_id: string;
  class_id: string;
  on_date: string;
  status: string;
}

export function markAttendance(payload: MarkAttendancePayload): Promise<{ id: string }> {
  return apiPost<{ id: string }>("/attendance", payload);
}

// --- Academic ---
export interface SchoolClass {
  id: string;
  name: string;
  academic_year: string;
}

export interface SubjectItem {
  id: string;
  code: string;
  name: string;
}

export function listClasses(): Promise<SchoolClass[]> {
  return apiGet<SchoolClass[]>("/academic/classes");
}

export function createClass(payload: {
  name: string;
  academic_year: string;
}): Promise<{ id: string }> {
  return apiPost<{ id: string }>("/academic/classes", payload);
}

export function listSubjects(): Promise<SubjectItem[]> {
  return apiGet<SubjectItem[]>("/academic/subjects");
}

export function createSubject(payload: { code: string; name: string }): Promise<{ id: string }> {
  return apiPost<{ id: string }>("/academic/subjects", payload);
}

export function createEnrollment(payload: {
  student_id: string;
  class_id: string;
  academic_year: string;
}): Promise<{ id: string }> {
  return apiPost<{ id: string }>("/academic/enrollments", payload);
}

// --- Exams ---
export interface ExamItem {
  id: string;
  name: string;
  academic_year: string;
  term: string | null;
}

export interface MarkItem {
  id: string;
  student_id: string;
  subject_id: string;
  score: number;
  grade: string | null;
}

export interface ReportCardResult {
  id: string;
  average: number;
  gpa: number;
  overall_grade: string;
  subjects: { subject: string; score: number }[];
}

export function listExams(): Promise<ExamItem[]> {
  return apiGet<ExamItem[]>("/exams");
}

export function createExam(payload: {
  name: string;
  academic_year: string;
  term?: string;
}): Promise<{ id: string }> {
  return apiPost<{ id: string }>("/exams", payload);
}

export function listMarks(examinationId: string): Promise<MarkItem[]> {
  return apiGet<MarkItem[]>(`/exams/marks/${examinationId}`);
}

export function recordMark(payload: {
  examination_id: string;
  student_id: string;
  subject_id: string;
  score: number;
}): Promise<{ id: string; grade: string }> {
  return apiPost<{ id: string; grade: string }>("/exams/marks", payload);
}

export function generateReportCard(
  examinationId: string,
  studentId: string,
): Promise<ReportCardResult> {
  return apiPost<ReportCardResult>(`/exams/report-cards/${examinationId}/${studentId}`);
}

// --- Payroll ---
export interface PayrollItem {
  id: string;
  staff_id: string;
  period: string;
  gross: number;
  paye: number;
  net: number;
  status: string;
}

export function listPayroll(): Promise<PayrollItem[]> {
  return apiGet<PayrollItem[]>("/payroll");
}

export function runPayroll(payload: {
  staff_id: string;
  period: string;
  gross: number;
  allowances?: number;
  other_deductions?: number;
}): Promise<{ id: string; gross: number; paye: number; net: number }> {
  return apiPost<{ id: string; gross: number; paye: number; net: number }>("/payroll", payload);
}

// --- Staff & HR ---
export interface StaffItem {
  id: string;
  staff_no: string;
  name: string;
  designation: string | null;
}

export interface LeaveItem {
  id: string;
  staff_id: string;
  leave_type: string;
  start_date: string | null;
  end_date: string | null;
  status: string;
  reason: string | null;
}

export function listStaff(): Promise<StaffItem[]> {
  return apiGet<StaffItem[]>("/staff/staff");
}

export function createStaff(payload: {
  staff_no: string;
  full_name: string;
  designation?: string;
  email?: string;
}): Promise<{ id: string }> {
  return apiPost<{ id: string }>("/staff/staff", payload);
}

export function listLeaves(): Promise<LeaveItem[]> {
  return apiGet<LeaveItem[]>("/staff/leaves");
}

export function requestLeave(payload: {
  staff_id: string;
  leave_type: string;
  start_date: string;
  end_date: string;
  reason?: string;
}): Promise<{ id: string; status: string }> {
  return apiPost<{ id: string; status: string }>("/staff/leaves", payload);
}

export function decideLeave(
  leaveId: string,
  decision: "approved" | "rejected",
): Promise<{ id: string; status: string }> {
  return apiPatch<{ id: string; status: string }>(`/staff/leaves/${leaveId}`, { decision });
}

// --- Library ---
export interface BookItem {
  id: string;
  title: string;
  author: string | null;
  available: number;
  total: number;
}

export interface LoanItem {
  id: string;
  book_id: string;
  borrower_id: string;
  borrowed_at: string | null;
  due_at: string | null;
  returned_at: string | null;
}

export function listBooks(): Promise<BookItem[]> {
  return apiGet<BookItem[]>("/library/books");
}

export function addBook(payload: {
  title: string;
  author?: string;
  isbn?: string;
  total_copies?: number;
}): Promise<{ id: string }> {
  return apiPost<{ id: string }>("/library/books", payload);
}

export function listLoans(): Promise<LoanItem[]> {
  return apiGet<LoanItem[]>("/library/loans");
}

export function loanBook(payload: {
  book_id: string;
  borrower_id: string;
  days?: number;
}): Promise<{ id: string; due_at: string }> {
  return apiPost<{ id: string; due_at: string }>("/library/loans", payload);
}

export function returnBook(loanId: string): Promise<{ id: string }> {
  return apiPost<{ id: string }>(`/library/loans/${loanId}/return`);
}

// --- Hostel ---
export interface RoomItem {
  id: string;
  name: string;
  capacity: number;
}

export interface AllocationItem {
  id: string;
  room_id: string;
  student_id: string;
  academic_year: string;
}

export function listRooms(): Promise<RoomItem[]> {
  return apiGet<RoomItem[]>("/hostel/rooms");
}

export function createRoom(payload: {
  name: string;
  capacity?: number;
  gender?: string;
}): Promise<{ id: string }> {
  return apiPost<{ id: string }>("/hostel/rooms", payload);
}

export function listAllocations(): Promise<AllocationItem[]> {
  return apiGet<AllocationItem[]>("/hostel/allocations");
}

export function allocateRoom(payload: {
  room_id: string;
  student_id: string;
  academic_year: string;
}): Promise<{ id: string }> {
  return apiPost<{ id: string }>("/hostel/allocations", payload);
}

// --- Transport ---
export interface RouteItem {
  id: string;
  name: string;
  fee: number;
}

export interface AssignmentItem {
  id: string;
  route_id: string;
  student_id: string;
  stop_name: string | null;
}

export function listRoutes(): Promise<RouteItem[]> {
  return apiGet<RouteItem[]>("/transport/routes");
}

export function createRoute(payload: {
  name: string;
  fee?: number;
  capacity?: number;
}): Promise<{ id: string }> {
  return apiPost<{ id: string }>("/transport/routes", payload);
}

export function listAssignments(): Promise<AssignmentItem[]> {
  return apiGet<AssignmentItem[]>("/transport/assignments");
}

export function assignTransport(payload: {
  route_id: string;
  student_id: string;
  stop_name?: string;
}): Promise<{ id: string }> {
  return apiPost<{ id: string }>("/transport/assignments", payload);
}

// --- LMS ---
export interface CourseItem {
  id: string;
  title: string;
  description: string | null;
}

export interface LessonItem {
  id: string;
  title: string;
  content_url: string | null;
  position: number;
}

export function listCourses(): Promise<CourseItem[]> {
  return apiGet<CourseItem[]>("/lms/courses");
}

export function createCourse(payload: {
  title: string;
  subject_id?: string;
  description?: string;
}): Promise<{ id: string }> {
  return apiPost<{ id: string }>("/lms/courses", payload);
}

export function listLessons(courseId: string): Promise<LessonItem[]> {
  return apiGet<LessonItem[]>(`/lms/courses/${courseId}/lessons`);
}

export function createLesson(payload: {
  course_id: string;
  title: string;
  content_url?: string;
  position?: number;
}): Promise<{ id: string }> {
  return apiPost<{ id: string }>("/lms/lessons", payload);
}

// --- Communication ---
export interface NotificationItem {
  id: string;
  channel: string;
  subject: string | null;
  body: string;
  read: boolean;
}

export function listNotifications(recipientId: string): Promise<NotificationItem[]> {
  return apiGet<NotificationItem[]>(`/communication/notifications/${recipientId}`);
}

export function sendNotification(payload: {
  recipient_id: string;
  channel?: string;
  subject?: string;
  body: string;
}): Promise<{ id: string; channel: string; delivered_externally: boolean }> {
  return apiPost<{ id: string; channel: string; delivered_externally: boolean }>(
    "/communication/notifications",
    payload,
  );
}

// --- Documents ---
export interface DocumentItem {
  id: string;
  name: string;
  content_type: string | null;
  size: number | null;
}

export function listDocuments(): Promise<DocumentItem[]> {
  return apiGet<DocumentItem[]>("/documents");
}

export function registerDocument(payload: {
  name: string;
  storage_key: string;
  content_type: string;
  size_bytes?: number;
}): Promise<{ id: string }> {
  return apiPost<{ id: string }>("/documents", payload);
}

// --- Reports ---
export function studentCount(): Promise<{ active_students: number }> {
  return apiGet<{ active_students: number }>("/reports/students/count");
}

export interface RankingEntry {
  student_id: string;
  position: number;
}

export function examRanking(examinationId: string): Promise<RankingEntry[]> {
  return apiGet<RankingEntry[]>(`/reports/exams/${examinationId}/ranking`);
}

// --- AI assistant ---
export function aiStatus(): Promise<{ available: boolean }> {
  return apiGet<{ available: boolean }>("/ai/status");
}

export function aiReportComment(payload: {
  student_name: string;
  average: number;
  attendance_rate?: number;
}): Promise<{ comment: string; ai_used: boolean }> {
  return apiPost<{ comment: string; ai_used: boolean }>("/ai/report-comment", payload);
}

export function aiFeeReminder(payload: {
  student_name: string;
  balance: number;
  currency?: string;
}): Promise<{ message: string; ai_used: boolean }> {
  return apiPost<{ message: string; ai_used: boolean }>("/ai/fee-reminder", payload);
}
