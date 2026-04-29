import Link from "next/link";
import { api, type AnomalyRow, type TenderDetail } from "@/lib/api";
import { Shell, PageHeader } from "@/components/Shell";
import { Card, CardHeader } from "@/components/Card";
import { Badge } from "@/components/Badge";
import { DetectAnomaliesButton } from "./DetectAnomaliesButton";

export default async function AnomaliesPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const tenderId = parseInt(id, 10);

  const [tender, flags] = await Promise.all([
    api<TenderDetail>(`/tenders/${tenderId}`),
    api<AnomalyRow[]>(`/anomalies/by-tender/${tenderId}`).catch(() => [] as AnomalyRow[]),
  ]);

  const bySeverity = {
    critical: flags.filter((f) => f.severity === "critical").length,
    major: flags.filter((f) => f.severity === "major").length,
    minor: flags.filter((f) => f.severity === "minor").length,
  };

  return (
    <Shell>
      <PageHeader
        breadcrumbs={[{ href: "/", label: "Tenders" }, { href: `/tenders/${tenderId}`, label: tender.title }]}
        title="Cross-Bid Anomalies"
        subtitle="Pairwise patterns suggesting collusion, copy-paste experience claims, shared partners, or coordinated pricing. AI surfaces; officer disposes."
        actions={<DetectAnomaliesButton tenderId={tenderId} />}
      />

      <div className="grid grid-cols-3 gap-4 mb-8">
        <SeverityCard label="Critical" count={bySeverity.critical} tone="fail" hint="Likely cartel signal" />
        <SeverityCard label="Major" count={bySeverity.major} tone="warn" hint="Strong pattern, requires explanation" />
        <SeverityCard label="Minor" count={bySeverity.minor} tone="neutral" hint="Coincidental but worth noting" />
      </div>

      {flags.length === 0 ? (
        <Card>
          <div className="text-sm text-slate-600">
            No anomalies detected yet. Click <span className="font-medium">Re-run detection</span> above to scan all submitted bids.
          </div>
        </Card>
      ) : (
        <div className="grid gap-3">
          {flags.map((f) => (
            <Card key={f.id} className={f.severity === "critical" ? "border-red-300 bg-red-50/30" : f.severity === "major" ? "border-amber-300 bg-amber-50/30" : ""}>
              <div className="flex items-start gap-4">
                <SeverityPill severity={f.severity} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1.5">
                    <Badge tone="brand" className="font-mono">{f.flag_type}</Badge>
                    <Badge tone="info">similarity {Math.round(f.similarity * 100)}%</Badge>
                  </div>
                  <div className="text-sm font-semibold text-slate-900 mb-1">
                    <Link href={`/bids/${f.bid_a_id}`} className="hover:text-sky-700">{f.bid_a_vendor}</Link>
                    <span className="text-slate-400 mx-2">↔</span>
                    <Link href={`/bids/${f.bid_b_id}`} className="hover:text-sky-700">{f.bid_b_vendor}</Link>
                  </div>
                  <p className="text-sm text-slate-700 leading-relaxed">{f.explanation}</p>
                  <details className="mt-3">
                    <summary className="text-xs font-medium text-slate-500 cursor-pointer hover:text-slate-700">Evidence</summary>
                    <pre className="mt-2 text-xs bg-slate-900 text-slate-100 p-3 rounded-md overflow-x-auto">
{JSON.stringify(f.evidence, null, 2)}
                    </pre>
                  </details>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </Shell>
  );
}

function SeverityCard({ label, count, tone, hint }: { label: string; count: number; tone: "fail" | "warn" | "neutral"; hint: string }) {
  const accent = { fail: "border-l-red-500", warn: "border-l-amber-500", neutral: "border-l-slate-300" }[tone];
  return (
    <div className={`rounded-xl bg-white border border-slate-200 shadow-sm p-5 border-l-4 ${accent}`}>
      <div className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</div>
      <div className="mt-2 text-3xl font-semibold text-slate-900 tabular-nums">{count}</div>
      <div className="mt-1 text-xs text-slate-500">{hint}</div>
    </div>
  );
}

function SeverityPill({ severity }: { severity: "info" | "minor" | "major" | "critical" }) {
  const colors = {
    critical: "bg-red-600",
    major: "bg-amber-500",
    minor: "bg-slate-400",
    info: "bg-slate-300",
  }[severity];
  const labels = { critical: "!", major: "!", minor: "i", info: "i" };
  return <div className={`shrink-0 h-9 w-9 rounded-full grid place-items-center text-white font-bold ${colors}`}>{labels[severity]}</div>;
}
