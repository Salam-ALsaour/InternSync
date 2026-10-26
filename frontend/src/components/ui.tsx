/** Shared building blocks following the design system (Design 8.2): cards 12 px, controls 8 px, chips rounded,
 *  44 px touch targets, status shown as text plus colour. */
import { type ReactNode, useId } from "react";
import { useTranslation } from "react-i18next";
import { ApiError } from "../api/client";

type Tone = "primary" | "secondary" | "danger" | "ghost";

const BUTTON: Record<Tone, string> = {
  primary: "bg-primary text-white hover:bg-primary-active disabled:bg-ink-muted",
  secondary: "bg-white text-primary border border-line hover:bg-ground disabled:text-ink-muted",
  danger: "bg-white text-[#A61B1B] border border-[#E9B8B8] hover:bg-[#FCE8E8] disabled:text-ink-muted",
  ghost: "text-primary underline-offset-4 hover:underline disabled:text-ink-muted",
};

export function Button({
  tone = "primary",
  busy,
  className = "",
  children,
  ...rest
}: React.ButtonHTMLAttributes<HTMLButtonElement> & { tone?: Tone; busy?: boolean }) {
  return (
    <button
      type="button"
      {...rest}
      disabled={rest.disabled || busy}
      className={`inline-flex min-h-[44px] items-center justify-center gap-2 rounded-ctl px-4 text-sm font-semibold transition-colors disabled:cursor-not-allowed ${BUTTON[tone]} ${className}`}
    >
      {busy && <span className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />}
      {children}
    </button>
  );
}

export function Card({ title, actions, children, className = "" }: {
  title?: ReactNode;
  actions?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={`rounded-card border border-line bg-white p-5 ${className}`}>
      {(title || actions) && (
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          {title && <h2 className="text-lg font-bold text-ink">{title}</h2>}
          {actions && <div className="flex flex-wrap gap-2">{actions}</div>}
        </div>
      )}
      {children}
    </section>
  );
}

export function PageHeader({ title, subtitle, actions }: { title: ReactNode; subtitle?: ReactNode; actions?: ReactNode }) {
  return (
    <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
      <div>
        <h1 className="text-2xl font-bold text-ink">{title}</h1>
        {subtitle && <p className="mt-1 text-sm text-ink-muted">{subtitle}</p>}
      </div>
      {actions && <div className="flex flex-wrap gap-2">{actions}</div>}
    </div>
  );
}

const INPUT = "min-h-[44px] w-full rounded-ctl border border-line bg-white px-3 text-sm text-ink focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 disabled:bg-ground";

export function Field({ label, error, hint, children }: { label: ReactNode; error?: string; hint?: ReactNode;
  children: (id: string) => ReactNode }) {
  const id = useId();
  return (
    <div className="flex flex-col gap-1">
      <label htmlFor={id} className="text-sm font-medium text-ink">{label}</label>
      {children(id)}
      {hint && !error && <p className="text-xs text-ink-muted">{hint}</p>}
      {error && <p className="text-xs text-[#A61B1B]" role="alert">{error}</p>}
    </div>
  );
}

export function Input({ label, error, hint, ...rest }: React.InputHTMLAttributes<HTMLInputElement> & {
  label: ReactNode; error?: string; hint?: ReactNode }) {
  return (
    <Field label={label} error={error} hint={hint}>
      {(id) => <input id={id} {...rest} className={`${INPUT} ${rest.type === "file" ? "py-2" : ""}`} />}
    </Field>
  );
}

export function TextArea({ label, error, hint, ...rest }: React.TextareaHTMLAttributes<HTMLTextAreaElement> & {
  label: ReactNode; error?: string; hint?: ReactNode }) {
  return (
    <Field label={label} error={error} hint={hint}>
      {(id) => <textarea id={id} rows={4} {...rest} className={`${INPUT} py-2`} />}
    </Field>
  );
}

export function Select({ label, error, hint, options, placeholder, ...rest }:
  React.SelectHTMLAttributes<HTMLSelectElement> & { label: ReactNode; error?: string; hint?: ReactNode;
    options: { value: string; label: string }[]; placeholder?: string }) {
  return (
    <Field label={label} error={error} hint={hint}>
      {(id) => (
        <select id={id} {...rest} className={INPUT}>
          {placeholder !== undefined && <option value="">{placeholder}</option>}
          {options.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>
      )}
    </Field>
  );
}

export function Checkbox({ label, ...rest }: React.InputHTMLAttributes<HTMLInputElement> & { label: ReactNode }) {
  return (
    <label className="inline-flex min-h-[44px] cursor-pointer items-center gap-2 text-sm text-ink">
      <input type="checkbox" {...rest} className="h-4 w-4 accent-[#1F3864]" />
      {label}
    </label>
  );
}

const CHIP: Record<string, string> = {
  neutral: "text-[#4A5363] bg-[#EEF1F5]",
  info: "text-[#1F4E9A] bg-[#E6EEFB]",
  success: "text-[#1E6B34] bg-[#E3F3E7]",
  warning: "text-[#8A4B00] bg-[#FFF1D6]",
  danger: "text-[#A61B1B] bg-[#FCE8E8]",
  purple: "text-[#6B3FA0] bg-[#F1EAFB]",
};

const STATUS_TONE: Record<string, keyof typeof CHIP> = {
  draft: "neutral", pending: "warning", not_required: "neutral", open: "success", closed: "neutral",
  submitted: "info", published: "success", active: "success", accepted: "success", approved: "success",
  verified: "success", placed: "success", completed: "success", revision_requested: "purple", late: "warning",
  missing: "danger", closed_missing: "danger", rejected: "danger", declined: "danger", withdrawn: "neutral",
  cancelled: "danger", placement_cancelled: "danger", suspended: "danger", inactive: "neutral",
};

/** A status chip: the translated label and its colour, never colour alone. */
export function StatusChip({ status, label }: { status: string; label?: string }) {
  const { t } = useTranslation();
  const tone = CHIP[STATUS_TONE[status] ?? "neutral"];
  return (
    <span className={`inline-flex items-center whitespace-nowrap rounded-full px-3 py-1 text-xs font-semibold ${tone}`}>
      {label ?? t(`status.${status}`)}
    </span>
  );
}

export function Chip({ children, tone = "neutral" }: { children: ReactNode; tone?: keyof typeof CHIP }) {
  return <span className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold ${CHIP[tone]}`}>{children}</span>;
}

/** Every AI result sits in a panel labelled Advisory (SRS 4.1, Design 8.3). */
export function Advisory({ children }: { children: ReactNode }) {
  const { t } = useTranslation();
  return (
    <div className="rounded-card border border-[#F3D3B5] bg-advisory-bg p-4 text-advisory-fg">
      <p className="mb-2 text-xs font-bold uppercase tracking-wide">{t("common.advisory")}</p>
      {children}
    </div>
  );
}

export function ErrorBox({ error }: { error: unknown }) {
  const { t } = useTranslation();
  if (!error) return null;
  const message = error instanceof ApiError ? error.detail : t("common.unexpected_error");
  const fields = error instanceof ApiError ? error.errors.filter((e) => e.message) : [];
  return (
    <div role="alert" className="rounded-ctl border border-[#E9B8B8] bg-[#FCE8E8] p-3 text-sm text-[#A61B1B]">
      <p>{message}</p>
      {fields.length > 0 && (
        <ul className="mt-1 list-disc ps-5">
          {fields.map((f) => <li key={f.field + f.code}>{f.message}</li>)}
        </ul>
      )}
    </div>
  );
}

export function Notice({ children, tone = "info" }: { children: ReactNode; tone?: "info" | "success" | "warning" }) {
  const cls = { info: "border-[#C7D6F2] bg-[#E6EEFB] text-[#1F4E9A]", success: "border-[#BFE0C8] bg-[#E3F3E7] text-[#1E6B34]",
    warning: "border-[#F2D9A6] bg-[#FFF1D6] text-[#8A4B00]" }[tone];
  return <div className={`rounded-ctl border p-3 text-sm ${cls}`}>{children}</div>;
}

export function Loading() {
  const { t } = useTranslation();
  return <p className="py-8 text-center text-sm text-ink-muted" aria-live="polite">{t("common.loading")}</p>;
}

export function Empty({ children }: { children?: ReactNode }) {
  const { t } = useTranslation();
  return <p className="rounded-ctl border border-dashed border-line p-6 text-center text-sm text-ink-muted">{children ?? t("common.empty")}</p>;
}

export function Table({ head, children }: { head: ReactNode[]; children: ReactNode }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[560px] border-collapse text-sm">
        <thead>
          <tr className="bg-ground text-start text-ink-muted">
            {head.map((h, i) => <th key={i} className="px-3 py-3 text-start font-semibold">{h}</th>)}
          </tr>
        </thead>
        <tbody className="divide-y divide-line">{children}</tbody>
      </table>
    </div>
  );
}

export function Td({ children, className = "" }: { children?: ReactNode; className?: string }) {
  return <td className={`px-3 py-3 align-top ${className}`}>{children}</td>;
}

export function Tabs<T extends string>({ value, onChange, items }: { value: T; onChange: (v: T) => void;
  items: { value: T; label: ReactNode }[] }) {
  return (
    <div role="tablist" className="mb-4 flex flex-wrap gap-2 border-b border-line">
      {items.map((it) => (
        <button key={it.value} type="button" role="tab" aria-selected={value === it.value}
          onClick={() => onChange(it.value)}
          className={`min-h-[44px] border-b-2 px-4 text-sm font-semibold ${value === it.value ? "border-primary text-primary" : "border-transparent text-ink-muted hover:text-ink"}`}>
          {it.label}
        </button>
      ))}
    </div>
  );
}

/** A small dialog for actions that need a reason (reject, cancel, close-missing, move a deadline). */
export function Dialog({ open, title, children, onClose }: { open: boolean; title: ReactNode; children: ReactNode;
  onClose: () => void }) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" role="dialog" aria-modal="true"
      onClick={onClose}>
      <div className="w-full max-w-lg rounded-card bg-white p-5 shadow-xl" onClick={(e) => e.stopPropagation()}>
        <h2 className="mb-4 text-lg font-bold">{title}</h2>
        {children}
      </div>
    </div>
  );
}

export function DefList({ items }: { items: [ReactNode, ReactNode][] }) {
  return (
    <dl className="grid grid-cols-1 gap-3 sm:grid-cols-2">
      {items.map(([k, v], i) => (
        <div key={i}>
          <dt className="text-xs text-ink-muted">{k}</dt>
          <dd className="text-sm font-medium text-ink">{v}</dd>
        </div>
      ))}
    </dl>
  );
}
