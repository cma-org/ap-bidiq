import Link from "next/link";
import { api, type BidListItem, type EvalStatementResponse, type TenderDetail } from "@/lib/api";
import { Shell, PageHeader } from "@/components/Shell";
import { Card, CardHeader } from "@/components/Card";
import { Badge, VerdictBadge } from "@/components/Badge";
import { fmtCr, fmtDate } from "@/lib/format";
import { ValidateAllButton } from "./ValidateAllButton";

export default async function BidsPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const tenderId = parseInt(id, 10);

  const [tender, bids] = await Promise.all([
    api<TenderDetail>(`/tenders/${tenderId}`),
    api<BidListItem[]>(`/bids?tender_id=${tenderId}`),
  ]);

  // Per-bid eval (best-effort; some bids may not have one yet)
  const evals = await Promise.all(
    bids.map((b) => api<EvalStatementResponse>(`/eval/by-bid/${b.id}`).catch(() => null))
  );

  const qualifiedCount = evals.filter((e) => e?.verdict === "qualified").length;

  return (
    <Shell>
      <PageHeader
        breadcrumbs={[{ href: "/", label: "Tenders" }, { href: `/tenders/${tenderId}`, label: tender.title }]}
        title="Submitted Bids"
        subtitle={`${bids.length} bids · ${qualifiedCount} qualified · evaluated under ActiveRules v2 (post-Corrigendum-1)`}
        actions={<ValidateAllButton tenderId={tenderId} />}
      />

      <div className="grid gap-3">
        {bids.map((b, i) => {
          const ev = evals[i];
          return (
            <Link key={b.id} href={`/bids/${b.id}`} className="block group">
              <Card className="hover:border-sky-400 hover:shadow-md transition" padded={false}>
                <div className="px-5 py-4 flex items-center gap-5">
                  <div className="h-11 w-11 rounded-lg bg-gradient-to-br from-slate-700 to-slate-900 grid place-items-center text-white font-semibold shrink-0">
                    {b.vendor_name.split(/\s+/).slice(0, 2).map((w) => w[0]).join("").toUpperCase().slice(0, 2)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-0.5">
                      <h3 className="text-base font-semibold text-slate-900 group-hover:text-sky-800 truncate">
                        {b.vendor_name}
                      </h3>
                      {b.jv_partners.length > 1 && <Badge tone="info">JV — {b.jv_partners.length} partners</Badge>}
                    </div>
                    <div className="flex items-center gap-3 text-xs text-slate-500">
                      <span>Bid value: <span className="font-medium text-slate-700">{fmtCr(b.bid_value_inr)}</span></span>
                      <span>•</span>
                      <span>Submitted {fmtDate(b.submitted_at)}</span>
                      <span>•</span>
                      <span>{b.extraction_count} forms extracted</span>
                    </div>
                  </div>
                  <div className="shrink-0">
                    {ev ? <VerdictBadge verdict={ev.verdict} /> : <Badge tone="neutral">Pending</Badge>}
                  </div>
                  <div className="text-slate-400 group-hover:text-sky-600 transition">→</div>
                </div>
              </Card>
            </Link>
          );
        })}
      </div>

      {bids.length === 0 && (
        <Card>
          <div className="text-sm text-slate-600">
            No bids found for this tender. Run <code className="font-mono text-xs bg-slate-100 px-1.5 py-0.5 rounded">python -m app.cli seed-bids</code> in the api folder.
          </div>
        </Card>
      )}
    </Shell>
  );
}
