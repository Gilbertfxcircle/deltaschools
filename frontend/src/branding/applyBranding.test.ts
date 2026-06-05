import { beforeEach, describe, expect, it } from "vitest";
import { applyBranding, DEFAULT_PRIMARY, DEFAULT_SECONDARY } from "@/branding/applyBranding";

function makeRoot(): HTMLElement {
  return document.createElement("div");
}

describe("applyBranding (per-tenant isolation - section 11)", () => {
  let root: HTMLElement;
  beforeEach(() => {
    root = makeRoot();
  });

  it("applies a tenant's colors", () => {
    applyBranding({ primary_color: "#abcdef", secondary_color: "#123456" }, { root });
    expect(root.style.getPropertyValue("--brand-primary")).toBe("#abcdef");
    expect(root.style.getPropertyValue("--brand-secondary")).toBe("#123456");
  });

  it("does NOT leak a previous tenant's theme on the next load", () => {
    applyBranding({ primary_color: "#abcdef" }, { root });
    // Next tenant provides no colors -> must reset to defaults, not keep #abcdef.
    applyBranding({}, { root });
    expect(root.style.getPropertyValue("--brand-primary")).toBe(DEFAULT_PRIMARY);
    expect(root.style.getPropertyValue("--brand-secondary")).toBe(DEFAULT_SECONDARY);
  });

  it("ignores invalid color values (falls back to defaults)", () => {
    applyBranding({ primary_color: "red; background:url(x)" }, { root });
    expect(root.style.getPropertyValue("--brand-primary")).toBe(DEFAULT_PRIMARY);
  });

  it("invokes setFavicon/setTitle hooks when provided", () => {
    let favicon = "";
    let title = "";
    applyBranding(
      { favicon_url: "/f.svg", school_motto: "Knowledge is Power" },
      { root, setFavicon: (u) => (favicon = u), setTitle: (t) => (title = t) },
    );
    expect(favicon).toBe("/f.svg");
    expect(title).toContain("Knowledge is Power");
  });
});
