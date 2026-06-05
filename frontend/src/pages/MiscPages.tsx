// Small standalone pages: Forbidden (403), NotFound (404), and a generic
// placeholder for modules that are enabled but whose UI is not built yet.

import { Link } from "react-router-dom";
import { Card, PageTitle } from "@/components/ui";

export function ForbiddenPage(): JSX.Element {
  return (
    <div className="space-y-3">
      <PageTitle>Access denied</PageTitle>
      <Card>
        <p className="text-sm text-slate-600">
          You do not have permission to view this page. If you believe this is an
          error, contact your school administrator.
        </p>
        <Link to="/" className="mt-3 inline-block text-sm" style={{ color: "var(--brand-primary)" }}>
          Back to dashboard
        </Link>
      </Card>
    </div>
  );
}

export function NotFoundPage(): JSX.Element {
  return (
    <div className="space-y-3">
      <PageTitle>Page not found</PageTitle>
      <Card>
        <Link to="/" className="text-sm" style={{ color: "var(--brand-primary)" }}>
          Back to dashboard
        </Link>
      </Card>
    </div>
  );
}

export function ModulePlaceholder({ title }: { title: string }): JSX.Element {
  return (
    <div className="space-y-3">
      <PageTitle>{title}</PageTitle>
      <Card>
        <p className="text-sm text-slate-600">
          This module is enabled for your institution. Its full interface is part
          of an upcoming release.
        </p>
      </Card>
    </div>
  );
}
