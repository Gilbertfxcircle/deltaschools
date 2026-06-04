import { describe, expect, it } from "vitest";
import { visibleNav, type NavItem } from "@/nav/navConfig";
import type { ModuleKey } from "@/api/types";

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
