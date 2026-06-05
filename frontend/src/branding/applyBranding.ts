// Branding engine (section 11). Applies a tenant's branding to the document by
// setting CSS custom properties and the favicon/title. Crucially, it RESETS to
// defaults first, so switching tenants never leaks one school's theme into the
// next (the brief calls this out explicitly, and it is unit-tested).

import type { Branding } from "@/api/types";

export const DEFAULT_PRIMARY = "#1d4ed8";
export const DEFAULT_SECONDARY = "#0f766e";

const HEX_RE = /^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$/;

function safeColor(value: string | undefined, fallback: string): string {
  return value && HEX_RE.test(value) ? value : fallback;
}

export interface BrandingTarget {
  root: HTMLElement;
  setFavicon?: (url: string) => void;
  setTitle?: (title: string) => void;
}

/** Apply branding to a target (defaults to document). Always resets first. */
export function applyBranding(branding: Branding, target?: BrandingTarget): void {
  const root = target?.root ?? document.documentElement;

  // Reset to defaults so previous tenant values cannot persist.
  root.style.setProperty("--brand-primary", DEFAULT_PRIMARY);
  root.style.setProperty("--brand-secondary", DEFAULT_SECONDARY);

  root.style.setProperty(
    "--brand-primary",
    safeColor(branding.primary_color, DEFAULT_PRIMARY),
  );
  root.style.setProperty(
    "--brand-secondary",
    safeColor(branding.secondary_color, DEFAULT_SECONDARY),
  );

  if (branding.favicon_url) {
    if (target?.setFavicon) {
      target.setFavicon(branding.favicon_url);
    } else if (typeof document !== "undefined") {
      const link = document.getElementById("app-favicon") as HTMLLinkElement | null;
      if (link) {
        link.href = branding.favicon_url;
      }
    }
  }

  if (branding.school_motto) {
    const title = `Delta Plax - ${branding.school_motto}`;
    if (target?.setTitle) {
      target.setTitle(title);
    } else if (typeof document !== "undefined") {
      document.title = title;
    }
  }
}

/** Reset branding to platform defaults (e.g. on logout / platform host). */
export function resetBranding(target?: BrandingTarget): void {
  applyBranding({}, target);
}
