// Tiny presentational primitives (Tailwind). Keeps pages terse without pulling
// in a full component library; shadcn/ui can be layered in later.

import type { ButtonHTMLAttributes, InputHTMLAttributes, ReactNode } from "react";

export function Button({
  children,
  className = "",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { children: ReactNode }): JSX.Element {
  return (
    <button
      {...props}
      className={[
        "rounded px-4 py-2 text-sm font-medium text-white disabled:opacity-50",
        className,
      ].join(" ")}
      style={{ background: "var(--brand-primary)", ...(props.style ?? {}) }}
    >
      {children}
    </button>
  );
}

export function Input(props: InputHTMLAttributes<HTMLInputElement>): JSX.Element {
  return (
    <input
      {...props}
      className={[
        "w-full rounded border border-slate-300 px-3 py-2 text-sm",
        "focus:outline-none focus:ring-2 focus:ring-offset-1",
        props.className ?? "",
      ].join(" ")}
    />
  );
}

export function Card({ children }: { children: ReactNode }): JSX.Element {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">{children}</div>
  );
}

export function PageTitle({ children }: { children: ReactNode }): JSX.Element {
  return <h1 className="mb-4 text-xl font-semibold text-slate-900">{children}</h1>;
}

export function ErrorText({ children }: { children: ReactNode }): JSX.Element | null {
  if (!children) {
    return null;
  }
  return <p className="text-sm text-red-600">{children}</p>;
}
