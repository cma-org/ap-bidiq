import Link from "next/link";
import { api, type EvalStatementResponse, type ValidationsResponse, type BidListItem, type TenderDetail } from "@/lib/api";
import { Shell, PageHeader } from "@/components/Shell";
import { Card, CardHeader, StatCard } from "@/components/Card";
import { Badge, VerdictBadge } from "@/components/Badge";
import { fmtCr, fmtDate } from "@/lib/format";
import { Scorecard } from "./Scorecard";

export default async function BidPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const bidId = parseInt(id, 10);

  const bid = await api<BidListItem & { extractions: { form_no: string; confidence: number; payload: Record<string, unknown> }[]; notes: string }>(`/bids/${bidId}`);
  const tender = await api<TenderDetail>(`/tenders/${bid.tender_id}`);
  const validations = await api<ValidationsResponse>(`/validations/by-bid/${bidId}`).catch(() => null);
  const evalStmt = await api<EvalStatementResponse>(`/eval/by-bid/${bidId}`).catch(() => null);

  const totalChecks = validations?.findings.length ?? 0;
  const passCount = validations?.summary.pass ?? 0;
  const failCount = validations?.summary.fail ?? 0;
  const warnCount = validations?.summary.warning ?? 0;

  return (
    <Shell>
      <PageHeader
        breadcrumbs={[
          { href: "/", label: "Tenders" },
          { href: `/tenders/${bid.tender_id}`, label: tender.title },
          { href: `/tenders/${bid.tender_id}/bids`, label: "Bids" },
        ]}
        title={bid.vendor_name}
        subtitle={
          <span className="flex items-center gap-3">
            <span>Bid value <span className="font-medium text-slate-900">{fmtCr(bid.bid_value_inr)}</span></span>
            <span className="text-slate-300">·</span>
            <span>Submitted {fmtDate(bid.submitted_at)}</span>
            {bid.jv_partners.length > 1 && (
              <>
                <span className="text-slate-300">·</span>
                <Badge tone="info">JV — {bid.jv_partners.length} partners</Badge>
              </>
            )}
          </span>
        }
        actions={evalStmt && <VerdictBadge verdict={evalStmt.verdict} />}
      />

      <div className="grid grid-cols-4 gap-4 mb-8">
        <StatCard
          label="Total checks"
          value={totalChecks}
          tone="neutral"
          hint="Layer 1 deterministic"
        />
        <StatCard
          label="Passing"
          value={passCount}
          tone="pass"
        />
        <StatCard
          label="Failing"
          value={failCount}
          tone="fail"
        />
        <StatCard
          label="Warnings"
          value={warnCount}
          tone="warn"
        />
      </div>

      {evalStmt?.verdict === "not_qualified" && evalStmt.reasons.length > 0 && (
        <Card className="mb-6 border-red-200 bg-red-50/40">
          <CardHeader
            title="Disqualification reasons"
            subtitle="The bid fails the following mandatory checks. Each cites the source clause; the officer can verify in seconds."
          />
          <ol className="space-y-2.5 list-decimal list-inside marker:text-red-700 marker:font-semibold">
            {evalStmt.reasons.map((r) => (
              <li key={r.check_id} className="text-sm text-slate-800">
                <span className="font-medium">{r.title}</span>
                <span className="text-slate-600"> — {r.message}</span>
              </li>
            ))}
          </ol>
        </Card>
      )}

      {evalStmt?.verdict === "qualified" && (
        <Card className="mb-6 border-emerald-200 bg-emerald-50/40">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-full bg-emerald-600 grid place-items-center text-white text-lg font-bold">✓</div>
            <div>
              <div className="text-sm font-semibold text-emerald-900">Bid qualifies for financial evaluation</div>
              <div className="text-xs text-emerald-800 mt-0.5">All 10 mandatory checks passed under ActiveRules v{evalStmt.json_payload.active_rules_version}. Proceeds to L1 (lowest evaluated bid) round.</div>
            </div>
          </div>
        </Card>
      )}

      <Card>
        <CardHeader
          title="Compliance Scorecard"
          subtitle="Click a finding to see its source citation in the tender."
        />
        {validations ? (
          <Scorecard findings={validations.findings} />
        ) : (
          <div className="text-sm text-slate-600 py-4">
            No validations yet. Use <span className="font-mono">Re-evaluate all bids</span> on the bids page.
          </div>
        )}
      </Card>

      {evalStmt && (
        <Card className="mt-6">
          <CardHeader
            title="Evaluation Statement"
            subtitle="Mirrors the AP human-evaluator format — drop-in replacement for the manual checklist."
          />
          <EvaluationStatementTable rows={evalStmt.json_payload.rows} />
        </Card>
      )}
    </Shell>
  );
}

function EvaluationStatementTable({ rows }: { rows: EvalStatementResponse["json_payload"]["rows"] }) {
  return (
    <div className="overflow-x-auto rounded-lg border border-slate-200">
      <table className="min-w-full text-sm">
        <thead className="bg-slate-900 text-slate-100">
          <tr>
            <th className="text-left px-3 py-2 text-xs font-semibold uppercase tracking-wide">Check</th>
            <th className="text-left px-3 py-2 text-xs font-semibold uppercase tracking-wide">Criterion</th>
            <th className="text-left px-3 py-2 text-xs font-semibold uppercase tracking-wide">Required</th>
            <th className="text-left px-3 py-2 text-xs font-semibold uppercase tracking-wide">Submitted</th>
            <th className="text-center px-3 py-2 text-xs font-semibold uppercase tracking-wide">Meets</th>
            <th className="text-left px-3 py-2 text-xs font-semibold uppercase tracking-wide">Remarks</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {rows.map((r) => (
            <tr key={r.check_id} className={r.verdict === "fail" ? "bg-red-50/40" : ""}>
              <td className="px-3 py-2 align-top font-mono text-xs text-slate-600">{r.check_id}</td>
              <td className="px-3 py-2 align-top text-slate-900 font-medium">{r.criterion}</td>
              <td className="px-3 py-2 align-top text-slate-700">{r.required}</td>
              <td className="px-3 py-2 align-top text-slate-700">{r.submitted}</td>
              <td className="px-3 py-2 align-top text-center">
                {r.meets ? (
                  <span className="inline-block text-emerald-700 font-bold">✓</span>
                ) : (
                  <span className="inline-block text-red-700 font-bold">✗</span>
                )}
              </td>
              <td className="px-3 py-2 align-top text-slate-700 text-xs leading-relaxed max-w-md">{r.remarks}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
