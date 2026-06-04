import { describe, expect, it } from "vitest";
import { ApiError, unwrap } from "@/api/client";
import type { ApiEnvelope } from "@/api/types";

describe("unwrap (response envelope handling)", () => {
  it("returns data on success", () => {
    const env: ApiEnvelope<{ id: string }> = {
      success: true,
      data: { id: "x1" },
      message: "OK",
      errors: [],
    };
    expect(unwrap(env)).toEqual({ id: "x1" });
  });

  it("throws ApiError carrying message + errors on failure", () => {
    const env: ApiEnvelope<null> = {
      success: false,
      data: null,
      message: "Missing required permission: students:write",
      errors: ["forbidden"],
    };
    try {
      unwrap(env);
      throw new Error("should have thrown");
    } catch (e) {
      expect(e).toBeInstanceOf(ApiError);
      const err = e as ApiError;
      expect(err.message).toContain("students:write");
      expect(err.errors).toEqual(["forbidden"]);
    }
  });
});
