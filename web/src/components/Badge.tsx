import type { ReactNode } from "react";

type Tone = "neutral" | "brand" | "pass" | "fail" | "warn" | "info";

const TONE: Record<Tone, string> = {
  neutral: "bg-slate-100 text-slate-700 ring-slate-200",
  brand: "bg-sky-100 text-sky-900 ring-sky-200",
  pass: "bg-emerald-50 text-emerald-800 ring-emerald-200",
  fail: "bg-red-50 text-red-800 ring-red-200",
  warn: "bg-amber-50 text-amber-900 ring-amber-200",
  info: "bg-cyan-50 text-cyan-900 ring-cyan-200",
};

export function Badge({
  children,
  tone = "neutral",
  className = "",
}: {
  children: ReactNode;
  tone?: Tone;
  className?: string;
}) {
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${TONE[tone]} ${className}`}
    >
      {children}
    </span>
  );
}

export function VerdictBadge({ verdict }: { verdict: string }) {
  if (verdict === "qualified" || verdict === "Qualified" || verdict === "pass")
    return <Badge tone="pass">✓ Qualified</Badge>;
  if (verdict === "not_qualified" || verdict === "Not Qualified" || verdict === "fail")
    return <Badge tone="fail">✗ Not Qualified</Badge>;
  if (verdict === "conditional" || verdict === "warning")
    return <Badge tone="warn">⚠ Conditional</Badge>;
  return <Badge tone="neutral">{verdict}</Badge>;
}
