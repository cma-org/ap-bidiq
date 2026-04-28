import Link from "next/link";
import { api, type BenchmarkResponse, type TenderDetail } from "@/lib/api";
import { Shell, PageHeader } from "@/components/Shell";
import { Card, CardHeader, StatCard } from "@/components/Card";
import { Badge } from "@/components/Badge";
import { fmtPct } from "@/lib/format";

export default async function BenchmarkPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const tenderId = parseInt(id, 10);

  const [tender, bench] = await Promise.all([
    api<TenderDetail>(`/tenders/${tenderId}`),
    api<BenchmarkResponse>(`/benchmark?tender_id=${tenderId}`),
  ]);

  return (
    <Shell>
      <PageHeader
        breadcrumbs={[{ href: "/", label: "Tenders" }, { href: `/tenders/${tenderId}`, label: tender.title }]}
        title="Accuracy Benchmark"
        subtitle="Live performance of AP-BidIQ vs. human-expert ground truth on the synthetic test set."
      />

      <div className="grid grid-cols-4 gap-4 mb-8">
        <StatCard
          label="Bids in benchmark"
          value={bench.bid_count}
          tone="neutral"
          hint="1 clean + 4 with planted defects"
        />
        <StatCard
          label="Defect detection"
          value={fmtPct(bench.defect_detection_rate)}
          tone={bench.defect_detection_rate >= 0.85 ? "pass" : "fail"}
          hint="Brief target: ≥ 85%"
        />
        <StatCard
          label="Verdict match"
          value={fmtPct(bench.verdict_match_rate)}
          tone={bench.verdict_match_rate >= 0.9 ? "pass" : "fail"}
          hint="Brief target: ≥ 90%"
        />
        <StatCard
          label="False positives"
          value={bench.false_positive_count}
          tone={bench.false_positive_count === 0 ? "pass" : "warn"}
          hint="Lower is better"
        />
      </div>

      <Card>
        <CardHeader
          title="Per-bid breakdown"
          subtitle="Each row compares AP-BidIQ's verdict + findings against the ground-truth label for that synthetic bid."
        />
        <div className="overflow-x-auto rounded-lg border border-slate-200">
          <table className="min-w-full text-sm">
            <thead className="bg-slate-900 text-slate-100">
              <tr>
                <th className="text-left px-3 py-2 text-xs font-semibold uppercase tracking-wide">Vendor</th>
                <th className="text-left px-3 py-2 text-xs font-semibold uppercase tracking-wide">Expected</th>
                <th className="text-left px-3 py-2 text-xs font-semibold uppercase tracking-wide">Actual</th>
                <th className="text-center px-3 py-2 text-xs font-semibold uppercase tracking-wide">Match</th>
                <th className="text-left px-3 py-2 text-xs font-semibold uppercase tracking-wide">Expected findings</th>
                <th className="text-left px-3 py-2 text-xs font-semibold uppercase tracking-wide">Caught</th>
                <th className="text-left px-3 py-2 text-xs font-semibold uppercase tracking-wide">Missed</th>
                <th className="text-left px-3 py-2 text-xs font-semibold uppercase tracking-wide">False positives</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 bg-white">
              {bench.rows.map((r) => (
                <tr key={r.bid_id}>
                  <td className="px-3 py-2.5">
                    <Link href={`/bids/${r.bid_id}`} className="font-medium text-slate-900 hover:text-sky-700">
                      {r.vendor_name}
                    </Link>
                  </td>
                  <td className="px-3 py-2.5 text-slate-700">{r.expected_verdict}</td>
                  <td className="px-3 py-2.5">
                    <Badge tone={r.actual_verdict === "qualified" ? "pass" : "fail"}>
                      {r.actual_verdict}
                    </Badge>
                  </td>
                  <td className="px-3 py-2.5 text-center">
                    {r.verdict_match ? <span className="text-emerald-700 font-bold">✓</span> : <span className="text-red-700 font-bold">✗</span>}
                  </td>
                  <td className="px-3 py-2.5">
                    <CheckList items={r.expected_findings} tone="info" />
                  </td>
                  <td className="px-3 py-2.5">
                    <CheckList items={r.caught_findings} tone="pass" />
                  </td>
                  <td className="px-3 py-2.5">
                    <CheckList items={r.missed_findings} tone="fail" />
                  </td>
                  <td className="px-3 py-2.5">
                    <CheckList items={r.false_positives} tone="warn" />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </Shell>
  );
}

function CheckList({ items, tone }: { items: string[]; tone: "info" | "pass" | "fail" | "warn" }) {
  if (items.length === 0) return <span className="text-slate-300 text-xs">—</span>;
  return (
    <div className="flex flex-wrap gap-1">
      {items.map((id) => (
        <Badge key={id} tone={tone} className="font-mono">{id}</Badge>
      ))}
    </div>
  );
}
