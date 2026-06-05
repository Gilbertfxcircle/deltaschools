// Minimal, dependency-free JWT payload decoder (no verification - the server
// verifies signatures; the client only reads claims like role/permissions/exp).

import type { AccessClaims } from "@/api/types";

function base64UrlDecode(input: string): string {
  const pad = input.length % 4 === 0 ? "" : "=".repeat(4 - (input.length % 4));
  const base64 = (input + pad).replace(/-/g, "+").replace(/_/g, "/");
  // `atob` exists in browsers and in jsdom (test env). We deliberately avoid a
  // Node `Buffer` dependency so this module stays browser-only and needs no
  // @types/node.
  const binary = atob(base64);
  return decodeURIComponent(
    binary
      .split("")
      .map((c) => `%${("00" + c.charCodeAt(0).toString(16)).slice(-2)}`)
      .join(""),
  );
}

export function decodeAccessClaims(token: string): AccessClaims | null {
  const parts = token.split(".");
  if (parts.length !== 3) {
    return null;
  }
  try {
    const payload = JSON.parse(base64UrlDecode(parts[1])) as AccessClaims;
    return payload;
  } catch {
    return null;
  }
}

export function isExpired(claims: AccessClaims, skewSeconds = 10): boolean {
  if (!claims.exp) {
    return true;
  }
  const nowSec = Math.floor(Date.now() / 1000);
  return claims.exp - skewSeconds <= nowSec;
}
