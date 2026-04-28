import Link from "next/link";
import { api, type BidListItem, type EvalStatementResponse, type TenderDetail, type ValidationsResponse } from "@/lib/api";
import { Shell, PageHeader } from "@/components/Shell";
import { Card, CardHeader } from "@/components/Card";
import { Badge, VerdictBadge } from "@/components/Badge";
import { fmtCr } from "@/lib/format";

export default async function ComparePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const tenderId = parseInt(id, 10);

  const [tender, bids] = await Promise.all([
    api<TenderDetail>(`/tenders/${tenderId}`),
    api<BidListItem[]>(`/bids?tender_id=${tenderId}`),
  ]);

  const evals = await Promise.all(
    bids.map((b) => api<EvalStatementResponse>(`/eval/by-bid/${b.id}`).catch(() => null))
  );
  const valids = await Promise.all(
    bids.map((b) => api<ValidationsResponse>(`/validations/by-bid/${b.id}`).catch(() => null))
  );

  const checkIds = Array.from(
    new Set(valids.flatMap((v) => v?.findings.map((f) => f.check_id) || []))
  ).sort();

  const qualifiedBids = bids.filter((_, i) => evals[i]?.verdict === "qualified");

  return (
    <Shell>
      <PageHeader
        breadcrumbs={[{ href: "/", label: "Tenders" }, { href: `/tenders/${tenderId}`, label: tender.title }]}
        title="Bid Comparison"
        subtitle={`Side-by-side qualification matrix across all ${bids.length} bids. Only qualified bids proceed to L1 financial evaluation.`}
      />

      <Card className="mb-6 bg-sky-50/40 border-sky-200">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-full bg-sky-700 grid place-items-center text-white text-base font-bold">L1</div>
          <div>
            <div className="text-sm font-semibold text-sky-900">
              {qualifiedBids.length} of {bids.length} bids qualify for L1 financial evaluation
            </div>
            <div className="text-xs text-sky-800 mt-0.5">
              {qualifiedBids.length === 0
                ? "No bids qualify — re-tender required."
                : `Lowest evaluated bid wins: ${qualifiedBids.map((b) => b.vendor_name).join(", ")}.`}
            </div>
          </div>
        </div>
      </Card>

      <Card padded={false}>
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead className="bg-slate-900 text-slate-100 sticky top-0">
              <tr>
                <th className="text-left px-3 py-2.5 text-xs font-semibold uppercase tracking-wide">Vendor</th>
                <th className="text-right px-3 py-2.5 text-xs font-semibold uppercase tracking-wide">Bid Value</th>
                <th className="text-center px-3 py-2.5 text-xs font-semibold uppercase tracking-wide">Verdict</th>
                {checkIds.map((id) => (
                  <th key={id} className="text-center px-2 py-2.5 text-xs font-mono uppercase tracking-wide">
                    {id.replace("FR-VAL-", "")}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 bg-white">
              {bids.map((b, i) => {
                const v = valids[i];
                const e = evals[i];
                const findingsByCheck = new Map(v?.findings.map((f) => [f.check_id, f.verdict]));
                return (
                  <tr key={b.id}>
                    <td className="px-3 py-3">
                      <Link href={`/bids/${b.id}`} className="font-medium text-slate-900 hover:text-sky-700">
                        {b.vendor_name}
                      </Link>
                    </td>
                    <td className="px-3 py-3 text-right tabular-nums text-slate-700">{fmtCr(b.bid_value_inr)}</td>
                    <td className="px-3 py-3 text-center">
                      {e ? <VerdictBadge verdict={e.verdict} /> : <Badge tone="neutral">Pending</Badge>}
                    </td>
                    {checkIds.map((id) => (
                      <td key={id} className="px-2 py-3 text-center">
                        <CheckCell verdict={findingsByCheck.get(id)} />
                      </td>
                    ))}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Card>
    </Shell>
  );
}

function CheckCell({ verdict }: { verdict?: string }) {
  if (!verdict) return <span className="text-slate-300">—</span>;
  if (verdict === "pass") return <span className="text-emerald-600 font-bold">✓</span>;
  if (verdict === "fail") return <span className="text-red-600 font-bold">✗</span>;
  return <span className="text-amber-600 font-bold">!</span>;
}
