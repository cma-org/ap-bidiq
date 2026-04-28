export function fmtCr(value: number | null | undefined): string {
  if (value == null) return "—";
  return `₹${value.toLocaleString("en-IN", { maximumFractionDigits: 2 })} Cr`;
}

export function fmtPct(value: number, digits = 1): string {
  return `${(value * 100).toFixed(digits)}%`;
}

export function fmtDate(iso: string): string {
  try {
    const d = new Date(iso);
    return d.toLocaleString("en-IN", {
      day: "2-digit", month: "short", year: "numeric",
      hour: "2-digit", minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

export function fmtDateOnly(iso: string): string {
  try {
    const d = new Date(iso);
    return d.toLocaleString("en-IN", { day: "2-digit", month: "short", year: "numeric" });
  } catch {
    return iso;
  }
}

export const verdictLabel: Record<string, string> = {
  qualified: "Qualified",
  not_qualified: "Not Qualified",
  conditional: "Conditional",
};
