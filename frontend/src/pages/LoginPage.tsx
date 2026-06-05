// Login page with a two-step MFA flow. If the backend responds that MFA is
// required (roles L1-L5 with MFA enabled), we reveal a TOTP code field and
// resubmit. Lockout (429) messages surface via toMessage().

import { useState, type FormEvent } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useAuthStore } from "@/store/authStore";
import { useModuleStore } from "@/store/moduleStore";
import { useBrandingStore } from "@/store/brandingStore";
import { Button, Card, ErrorText, Input } from "@/components/ui";
import { toMessage } from "@/lib/errors";

export function LoginPage(): JSX.Element {
  const navigate = useNavigate();
  const location = useLocation();
  const doLogin = useAuthStore((s) => s.login);
  const loadModules = useModuleStore((s) => s.load);
  const loadBranding = useBrandingStore((s) => s.load);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [totp, setTotp] = useState("");
  const [mfaRequired, setMfaRequired] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: FormEvent): Promise<void> {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await doLogin({
        email,
        password,
        totp_code: mfaRequired && totp ? totp : undefined,
      });
      // Load tenant context after auth, then route to the intended page.
      await Promise.all([loadModules(), loadBranding()]);
      const dest = (location.state as { from?: string } | null)?.from ?? "/";
      navigate(dest, { replace: true });
    } catch (err) {
      const msg = toMessage(err);
      if (msg.toLowerCase().includes("mfa")) {
        setMfaRequired(true);
        setError("Enter your authenticator code to continue.");
      } else {
        setError(msg);
      }
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex h-full items-center justify-center bg-slate-100">
      <div className="w-full max-w-sm">
        <div
          className="mb-4 rounded-t-lg px-5 py-4 text-center text-lg font-semibold text-white"
          style={{ background: "var(--brand-primary)" }}
        >
          Delta Plax Education Suite
        </div>
        <Card>
          <form onSubmit={onSubmit} className="space-y-3">
            <label className="block text-sm">
              <span className="mb-1 block text-slate-600">Email</span>
              <Input
                type="email"
                autoComplete="username"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </label>
            <label className="block text-sm">
              <span className="mb-1 block text-slate-600">Password</span>
              <Input
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </label>
            {mfaRequired && (
              <label className="block text-sm">
                <span className="mb-1 block text-slate-600">Authenticator code</span>
                <Input
                  inputMode="numeric"
                  pattern="[0-9]*"
                  maxLength={6}
                  value={totp}
                  onChange={(e) => setTotp(e.target.value)}
                  placeholder="123456"
                />
              </label>
            )}
            <ErrorText>{error}</ErrorText>
            <Button type="submit" disabled={busy} className="w-full">
              {busy ? "Signing in..." : "Sign in"}
            </Button>
          </form>
        </Card>
        <p className="mt-4 text-center text-xs text-slate-400">
          &copy; 2026&ndash;2035 Delta Plax Technologies
        </p>
      </div>
    </div>
  );
}
