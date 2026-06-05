import { describe, expect, it } from "vitest";
import { hasPermission } from "@/lib/permissions";

describe("hasPermission (client RBAC mirror)", () => {
  it("matches exact permissions", () => {
    expect(hasPermission(["students:read"], "students:read")).toBe(true);
    expect(hasPermission(["students:read"], "students:write")).toBe(false);
  });

  it("honours resource wildcards", () => {
    expect(hasPermission(["students:*"], "students:write")).toBe(true);
    expect(hasPermission(["students:*"], "marks:write")).toBe(false);
  });

  it("honours the global wildcard", () => {
    expect(hasPermission(["*"], "anything:goes")).toBe(true);
  });

  it("returns false for an empty grant set", () => {
    expect(hasPermission([], "students:read")).toBe(false);
  });
});
