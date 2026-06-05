// Tiny presentational primitives (Tailwind). Keeps pages terse without pulling
// in a full component library; shadcn/ui can be layered in later.

import type {
  ButtonHTMLAttributes,
  InputHTMLAttributes,
  ReactNode,
  SelectHTMLAttributes,
} from "react";

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

export function Select({
  children,
  ...props
}: SelectHTMLAttributes<HTMLSelectElement> & { children: ReactNode }): JSX.Element {
  return (
    <select
      {...props}
      className={[
        "w-full rounded border border-slate-300 bg-white px-3 py-2 text-sm",
        "focus:outline-none focus:ring-2 focus:ring-offset-1",
        props.className ?? "",
      ].join(" ")}
    >
      {children}
    </select>
  );
}

export interface Column<T> {
  header: string;
  /** Render a cell from a row. */
  cell: (row: T) => ReactNode;
}

export function DataTable<T>({
  columns,
  rows,
  loading,
  empty = "Nothing to show yet.",
  rowKey,
}: {
  columns: Column<T>[];
  rows: T[];
  loading?: boolean;
  empty?: string;
  rowKey: (row: T) => string;
}): JSX.Element {
  if (loading) {
    return <p className="text-sm text-slate-500">Loading...</p>;
  }
  if (rows.length === 0) {
    return <p className="text-sm text-slate-500">{empty}</p>;
  }
  return (
    <table className="w-full text-left text-sm">
      <thead>
        <tr className="border-b border-slate-200 text-slate-500">
          {columns.map((c) => (
            <th key={c.header} className="py-2 pr-4">
              {c.header}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((row) => (
          <tr key={rowKey(row)} className="border-b border-slate-100">
            {columns.map((c) => (
              <td key={c.header} className="py-2 pr-4">
                {c.cell(row)}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export function StatCard({ label, value }: { label: string; value: ReactNode }): JSX.Element {
  return (
    <Card>
      <p className="text-xs text-slate-500">{label}</p>
      <p className="text-lg font-semibold">{value}</p>
    </Card>
  );
}
