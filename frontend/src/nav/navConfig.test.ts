import { describe, expect, it } from "vitest";
import { NAV_ITEMS, visibleNav, type NavItem } from "@/nav/navConfig";
import type { ModuleKey } from "@/api/types";

const ALL_MODULES: ModuleKey[] = [
  "attendance",
  "billing",
  "payroll",
  "hostel",
  "library",
  "transport",
  "lms",
  "hr_management",
  "communication_hub",
  "document_management",
];

const ITEMS: NavItem[] = [
  { key: "dashboard", label: "Dashboard", path: "/" },
  { key: "students", label: "Students", path: "/students", permission: "students:read" },
  { key: "library", label: "Library", path: "/library", module: "library" },
  {
    key: "payroll",
    label: "Payroll",
    path: "/payroll",
    module: "payroll",
    permission: "payroll:read",
  },
];

describe("visibleNav (module + permission gating)", () => {
  it("hides items whose module is disabled (no greyed-out links)", () => {
    const enabled = new Set<ModuleKey>(["library"]);
    const nav = visibleNav(ITEMS, {
      isModuleEnabled: (k) => enabled.has(k),
      can: () => true,
    });
    const keys = nav.map((n) => n.key);
    expect(keys).toContain("library");
    expect(keys).not.toContain("payroll"); // module disabled -> absent entirely
  });

  it("hides items the user lacks permission for", () => {
    const nav = visibleNav(ITEMS, {
      isModuleEnabled: () => true,
      can: (p) => p === "students:read", // no payroll:read
    });
    const keys = nav.map((n) => n.key);
    expect(keys).toContain("students");
    expect(keys).not.toContain("payroll");
  });

  it("always shows ungated core items", () => {
    const nav = visibleNav(ITEMS, {
      isModuleEnabled: () => false,
      can: () => false,
    });
    expect(nav.map((n) => n.key)).toEqual(["dashboard"]);
  });
});

describe("NAV_ITEMS registry (real navigation)", () => {
  it("exposes every module page to a director with all modules enabled", () => {
    const enabled = new Set<ModuleKey>(ALL_MODULES);
    const nav = visibleNav(NAV_ITEMS, {
      isModuleEnabled: (k) => enabled.has(k),
      can: () => true, // director-style: full permissions
    });
    const keys = nav.map((n) => n.key);
    for (const key of [
      "students", "attendance", "exams", "billing", "payroll", "hr",
      "library", "hostel", "transport", "lms", "communication", "documents",
      "reports", "approvals", "audit",
    ]) {
      expect(keys).toContain(key);
    }
  });

  it("hides module pages when modules are disabled even with full permissions", () => {
    const nav = visibleNav(NAV_ITEMS, {
      isModuleEnabled: () => false, // no optional modules
      can: () => true,
    });
    const keys = nav.map((n) => n.key);
    // Module-gated pages disappear...
    expect(keys).not.toContain("library");
    expect(keys).not.toContain("payroll");
    expect(keys).not.toContain("hr");
    // ...but ungated core pages remain.
    expect(keys).toContain("dashboard");
    expect(keys).toContain("students");
    expect(keys).toContain("exams");
  });

  it("hides reports/audit/approvals from a user without those permissions", () => {
    const nav = visibleNav(NAV_ITEMS, {
      isModuleEnabled: () => true,
      can: (p) => p === "students:read",
    });
    const keys = nav.map((n) => n.key);
    expect(keys).toContain("students");
    expect(keys).not.toContain("reports");
    expect(keys).not.toContain("audit");
    expect(keys).not.toContain("approvals");
  });
});
