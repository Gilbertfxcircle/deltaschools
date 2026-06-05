import { describe, expect, it } from "vitest";
import { tenantFromHostname } from "@/api/tenant";

describe("tenantFromHostname", () => {
  it("extracts the tenant from a subdomain", () => {
    expect(tenantFromHostname("stmarys.deltaplax.com")).toBe("stmarys");
    expect(tenantFromHostname("demo.deltaplax.com:3000")).toBe("demo");
  });

  it("returns null for reserved/platform hosts", () => {
    expect(tenantFromHostname("admin.deltaplax.com")).toBeNull();
    expect(tenantFromHostname("www.deltaplax.com")).toBeNull();
    expect(tenantFromHostname("deltaplax.com")).toBeNull();
  });

  it("returns null for localhost and bare IPs", () => {
    expect(tenantFromHostname("localhost")).toBeNull();
    expect(tenantFromHostname("127.0.0.1")).toBeNull();
    expect(tenantFromHostname("192.168.1.10")).toBeNull();
  });
});
