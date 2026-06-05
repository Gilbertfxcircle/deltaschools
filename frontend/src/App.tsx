// Root component: hydrates auth from any stored token, loads tenant context
// (modules + branding) once authenticated, and defines the route tree.
// Feature routes are guarded both by permission (ProtectedRoute) and, where
// relevant, by module enablement.

import { useEffect } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { useAuthStore } from "@/store/authStore";
import { useModuleStore } from "@/store/moduleStore";
import { useBrandingStore } from "@/store/brandingStore";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { AppLayout } from "@/components/AppLayout";
import { LoginPage } from "@/pages/LoginPage";
import { DashboardPage } from "@/pages/DashboardPage";
import { StudentsPage } from "@/pages/StudentsPage";
import { BillingPage } from "@/pages/BillingPage";
import { ApprovalsPage } from "@/pages/ApprovalsPage";
import { AuditPage } from "@/pages/AuditPage";
import { ForbiddenPage, ModulePlaceholder, NotFoundPage } from "@/pages/MiscPages";
import type { ModuleKey } from "@/api/types";

/** Guard a route by module enablement; redirect to dashboard if disabled. */
function ModuleRoute({
  module,
  children,
}: {
  module: ModuleKey;
  children: JSX.Element;
}): JSX.Element {
  const isEnabled = useModuleStore((s) => s.isEnabled);
  const loaded = useModuleStore((s) => s.loaded);
  if (loaded && !isEnabled(module)) {
    return <Navigate to="/" replace />;
  }
  return children;
}

export default function App(): JSX.Element {
  const identity = useAuthStore((s) => s.identity);
  const initialized = useAuthStore((s) => s.initialized);
  const hydrate = useAuthStore((s) => s.hydrate);
  const loadModules = useModuleStore((s) => s.load);
  const loadBranding = useBrandingStore((s) => s.load);

  useEffect(() => {
    hydrate();
  }, [hydrate]);

  useEffect(() => {
    if (identity) {
      void loadModules();
      void loadBranding();
    }
  }, [identity, loadModules, loadBranding]);

  if (!initialized) {
    return <div className="p-6 text-sm text-slate-500">Loading...</div>;
  }

  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }
      >
        <Route path="/" element={<DashboardPage />} />
        <Route
          path="/students"
          element={
            <ProtectedRoute permission="students:read">
              <StudentsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/attendance"
          element={
            <ModuleRoute module="attendance">
              <ModulePlaceholder title="Attendance" />
            </ModuleRoute>
          }
        />
        <Route
          path="/billing"
          element={
            <ModuleRoute module="billing">
              <BillingPage />
            </ModuleRoute>
          }
        />
        <Route
          path="/payroll"
          element={
            <ModuleRoute module="payroll">
              <ModulePlaceholder title="Payroll" />
            </ModuleRoute>
          }
        />
        <Route
          path="/hr"
          element={
            <ModuleRoute module="hr_management">
              <ModulePlaceholder title="Staff & HR" />
            </ModuleRoute>
          }
        />
        <Route
          path="/library"
          element={
            <ModuleRoute module="library">
              <ModulePlaceholder title="Library" />
            </ModuleRoute>
          }
        />
        <Route
          path="/hostel"
          element={
            <ModuleRoute module="hostel">
              <ModulePlaceholder title="Hostel" />
            </ModuleRoute>
          }
        />
        <Route
          path="/transport"
          element={
            <ModuleRoute module="transport">
              <ModulePlaceholder title="Transport" />
            </ModuleRoute>
          }
        />
        <Route
          path="/lms"
          element={
            <ModuleRoute module="lms">
              <ModulePlaceholder title="E-Learning" />
            </ModuleRoute>
          }
        />
        <Route
          path="/communication"
          element={
            <ModuleRoute module="communication_hub">
              <ModulePlaceholder title="Communication" />
            </ModuleRoute>
          }
        />
        <Route
          path="/documents"
          element={
            <ModuleRoute module="document_management">
              <ModulePlaceholder title="Documents" />
            </ModuleRoute>
          }
        />
        <Route
          path="/reports"
          element={
            <ProtectedRoute permission="reports:read">
              <ModulePlaceholder title="Reports" />
            </ProtectedRoute>
          }
        />
        <Route
          path="/approvals"
          element={
            <ProtectedRoute permission="approvals:decide">
              <ApprovalsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/audit"
          element={
            <ProtectedRoute permission="audit:read">
              <AuditPage />
            </ProtectedRoute>
          }
        />
        <Route path="/forbidden" element={<ForbiddenPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}
