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
