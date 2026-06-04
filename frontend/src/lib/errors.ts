// Normalize errors (axios / ApiError / unknown) into a user-facing message,
// preserving the backend envelope's `message` and lockout/MFA hints.

import { AxiosError } from "axios";
import { ApiError } from "@/api/client";
import type { ApiEnvelope } from "@/api/types";

export function toMessage(err: unknown): string {
  if (err instanceof ApiError) {
    return err.message;
  }
  if (err instanceof AxiosError) {
    const data = err.response?.data as ApiEnvelope<unknown> | undefined;
    if (data?.message) {
      return data.message;
    }
    if (err.response?.status === 429) {
      return "Account locked due to repeated failed logins. Please try again later.";
    }
    return err.message;
  }
  if (err instanceof Error) {
    return err.message;
  }
  return "An unexpected error occurred";
}
