// Shared API types. Mirrors the backend's response envelope (section 16) and
// the core resource shapes. Strict typing: no `any`.

/** The standard envelope every backend response uses. */
export interface ApiEnvelope<T> {
  success: boolean;
  data: T;
  message: string;
  errors: string[];
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

/** Decoded fields we rely on from the JWT access token. */
export interface AccessClaims {
  sub: string;
  email: string;
  role: string;
  tenant: string | null;
  permissions: string[];
  exp: number;
  type: string;
}

export interface Branding {
  logo_url?: string;
  favicon_url?: string;
  primary_color?: string;
  secondary_color?: string;
  school_motto?: string;
  login_background_url?: string;
  certificate_template_id?: string;
  report_card_template_id?: string;
  receipt_header_text?: string;
  email_signature_html?: string;
}

export interface Student {
  id: string;
  admission_no: string;
  name: string;
  gender: string | null;
}

export interface ApprovalRequestSummary {
  id: string;
  resource: string;
  state: "pending" | "approved" | "rejected" | "applied";
  reason: string;
}

export interface AuditEntry {
  id: string;
  timestamp: string | null;
  user_email: string;
  action: string;
  resource: string;
  resource_id: string | null;
  approval_status: string;
}

/** Canonical module keys (section 7). Kept in sync with the backend registry. */
export type ModuleKey =
  | "attendance"
  | "billing"
  | "mobile_money"
  | "sms"
  | "payroll"
  | "hostel"
  | "library"
  | "transport"
  | "lms"
  | "parent_portal"
  | "student_portal"
  | "teacher_portal"
  | "mobile_apps"
  | "ai_assistant"
  | "communication_hub"
  | "biometric_attendance"
  | "hr_management"
  | "document_management";
