// Navigation registry. Each item may be gated by a module flag and/or a
// permission. visibleNav() drops items the tenant cannot see entirely (no
// greyed-out links), mirroring the backend's app/core/modules.visible_nav.

import type { ModuleKey } from "@/api/types";

export interface NavItem {
  key: string;
  label: string;
  path: string;
  /** Module that must be enabled for this item to appear (undefined = always). */
  module?: ModuleKey;
  /** Permission required to see this item (undefined = no permission gate). */
  permission?: string;
}

export const NAV_ITEMS: readonly NavItem[] = [
  { key: "dashboard", label: "Dashboard", path: "/" },
  { key: "students", label: "Students", path: "/students", permission: "students:read" },
  {
    key: "attendance",
    label: "Attendance",
    path: "/attendance",
    module: "attendance",
    permission: "attendance:read",
  },
  { key: "exams", label: "Examinations", path: "/exams", permission: "exams:read" },
  { key: "billing", label: "Billing", path: "/billing", module: "billing", permission: "finance:read" },
  { key: "payroll", label: "Payroll", path: "/payroll", module: "payroll", permission: "payroll:read" },
  { key: "hr", label: "Staff & HR", path: "/hr", module: "hr_management", permission: "staff:read" },
  { key: "library", label: "Library", path: "/library", module: "library" },
  { key: "hostel", label: "Hostel", path: "/hostel", module: "hostel" },
  { key: "transport", label: "Transport", path: "/transport", module: "transport" },
  { key: "lms", label: "E-Learning", path: "/lms", module: "lms" },
  {
    key: "communication",
    label: "Communication",
    path: "/communication",
    module: "communication_hub",
  },
  {
    key: "documents",
    label: "Documents",
    path: "/documents",
    module: "document_management",
    permission: "documents:read",
  },
  { key: "reports", label: "Reports", path: "/reports", permission: "reports:read" },
  { key: "approvals", label: "Approvals", path: "/approvals", permission: "approvals:decide" },
  { key: "audit", label: "Audit Log", path: "/audit", permission: "audit:read" },
];

export interface NavContext {
  isModuleEnabled: (key: ModuleKey) => boolean;
  can: (permission: string) => boolean;
}

/** Filter nav to items whose module is enabled AND whose permission is held. */
export function visibleNav(items: readonly NavItem[], ctx: NavContext): NavItem[] {
  return items.filter((item) => {
    if (item.module && !ctx.isModuleEnabled(item.module)) {
      return false;
    }
    if (item.permission && !ctx.can(item.permission)) {
      return false;
    }
    return true;
  });
}
