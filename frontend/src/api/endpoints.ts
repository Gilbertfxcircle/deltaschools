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
  return apiPost("/finance/payments", payload);
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
