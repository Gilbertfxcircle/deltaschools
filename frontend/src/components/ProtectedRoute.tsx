// Route guard. Redirects unauthenticated users to /login and blocks users who
// lack the required permission (server still re-checks every request).

import { Navigate, useLocation } from "react-router-dom";
import type { ReactNode } from "react";
import { useAuthStore } from "@/store/authStore";

interface ProtectedRouteProps {
  children: ReactNode;
  permission?: string;
}

export function ProtectedRoute({ children, permission }: ProtectedRouteProps): JSX.Element {
  const location = useLocation();
  const identity = useAuthStore((s) => s.identity);
  const can = useAuthStore((s) => s.can);

  if (!identity) {
    return <Navigate to="/login" state={{ from: location.pathname }} replace />;
  }
  if (permission && !can(permission)) {
    return <Navigate to="/forbidden" replace />;
  }
  return <>{children}</>;
}
