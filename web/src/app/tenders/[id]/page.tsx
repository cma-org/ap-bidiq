import Link from "next/link";
import { api, type ActiveRules, type CorrigendumDiff, type MandatoryClauseRow, type TenderDetail } from "@/lib/api";
import { Shell, PageHeader } from "@/components/Shell";
import { Card, CardHeader } from "@/components/Card";
import { Badge } from "@/components/Badge";

export default async function TenderPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const tenderId = parseInt(id, 10);

  const [tender, diff, rules, mandatory] = await Promise.all([
    api<TenderDetail>(`/tenders/${tenderId}`),
    api<CorrigendumDiff>(`/tenders/${tenderId}/corrigendum-diff`),
    api<ActiveRules>(`/tenders/${tenderId}/active-rules`),
    api<MandatoryClauseRow[]>(`/tenders/${tenderId}/mandatory-clauses`),
  ]);

  const thresholds = (rules.payload.thresholds || {}) as Record<string, number>;
  const formula = (rules.payload.bid_capacity_formula || {}) as Record<string, string | number>;

  return (
    <Shell>
      <PageHeader
        breadcrumbs={[{ href: "/", label: "Tenders" }]}
        title={tender.title}
        subtitle={tender.department}
        actions={
          <Link
            href={`/tenders/${tenderId}/bids`}
            className="rounded-lg bg-sky-700 hover:bg-sky-800 text-white text-sm font-medium px-4 py-2 shadow-sm transition"
          >
            View Bids →
          </Link>
        }
      />

      <div className="grid grid-cols-3 gap-4 mb-8">
        <SummaryStat label="Sections" value={tender.sections.length} />
        <SummaryStat label="Mandatory clauses" value={tender.mandatory_clauses_count} />
        <SummaryStat label="Forms required" value={tender.forms_required_count} />
      </div>

      {diff.corrigenda.length > 0 && (
        <Card className="mb-8 border-amber-200 bg-amber-50/40">
          <CardHeader
            title={
              <span className="flex items-center gap-2">
                <span>Corrigendum Diff</span>
                <Badge tone="warn">{diff.corrigenda.length} applied</Badge>
              </span>
            }
            subtitle="Amendments to the original tender that change effective rules. Bids submitted after these dates are evaluated against the post-corrigendum ruleset."
          />
          <div className="space-y-5">
            {diff.corrigenda.map((c) => (
              <div key={c.corrigendum_id}>
                <div className="text-sm font-semibold text-slate-900 mb-2">{c.name}</div>
                <div className="space-y-3">
                  {c.patches.map((p, i) => (
                    <div key={i} className="rounded-lg border border-amber-200 bg-white p-4">
                      <div className="flex items-center gap-2 mb-2">
                        <Badge tone="brand" className="font-mono">{p.target_clause}</Badge>
                        <Badge tone="warn">{p.op}</Badge>
                      </div>
                      {p.summary && <p className="text-sm text-slate-700 mb-3">{p.summary}</p>}
                      <div className="grid md:grid-cols-2 gap-3">
                        <DiffBlock label="Before" tone="fail" text={p.before} />
                        <DiffBlock label="After" tone="pass" text={p.after} />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      <div className="grid lg:grid-cols-2 gap-6 mb-8">
        <Card>
          <CardHeader
            title={<span>Active Rules <Badge tone="brand">v{rules.version}</Badge></span>}
            subtitle="Effective ruleset after applying all corrigenda."
          />
          <div className="space-y-4">
            <div>
              <div className="text-xs font-semibold uppercase tracking-wide text-slate-500 mb-1.5">Bid Capacity Formula</div>
              <div className="rounded-lg bg-slate-900 text-slate-100 px-3 py-2 font-mono text-sm">
                {String(formula.expression || "")}
              </div>
              <div className="mt-2 text-xs text-slate-600">
                A_lookback_years = <span className="font-semibold text-slate-900">{String(formula.A_lookback_years)}</span>
                {" · "}Pass: <code className="text-xs">{String(formula.pass_rule || "")}</code>
              </div>
            </div>
            <ThresholdsTable thresholds={thresholds} />
          </div>
        </Card>

        <Card>
          <CardHeader title="Mandatory Clauses" subtitle={`${mandatory.length} compliance items checked per bid`} />
          <div className="space-y-2 max-h-96 overflow-y-auto pr-2">
            {mandatory.map((m) => (
              <div key={m.id} className="flex items-start gap-3 py-2 border-b border-slate-100 last:border-0">
                <Badge tone={m.layer === "L1" ? "brand" : "info"} className="font-mono shrink-0">{m.layer}</Badge>
                <div className="min-w-0 flex-1">
                  <div className="text-sm font-medium text-slate-900">{m.title}</div>
                  <div className="text-xs text-slate-500 mt-0.5">{m.source_section}</div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      <Card>
        <CardHeader title="Sections in this tender package" />
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-2">
          {tender.sections.sort((a, b) => a.order_idx - b.order_idx).map((s) => (
            <div key={s.id} className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2">
              <div className="text-sm text-slate-900 font-medium">{s.name}</div>
              <div className="text-xs text-slate-500 mt-0.5">{s.char_count.toLocaleString()} chars</div>
            </div>
          ))}
        </div>
      </Card>
    </Shell>
  );
}

function SummaryStat({ label, value }: { label: string; value: number }) {
  return (
    <Card padded={false} className="px-5 py-4">
      <div className="text-xs uppercase tracking-wide text-slate-500 font-medium">{label}</div>
      <div className="mt-1 text-2xl font-semibold text-slate-900 tabular-nums">{value}</div>
    </Card>
  );
}

function DiffBlock({ label, tone, text }: { label: string; tone: "fail" | "pass"; text: string | null }) {
  const borderColor = tone === "fail" ? "border-red-200" : "border-emerald-200";
  const bgColor = tone === "fail" ? "bg-red-50/60" : "bg-emerald-50/60";
  const labelColor = tone === "fail" ? "text-red-800" : "text-emerald-800";
  return (
    <div className={`rounded-md border ${borderColor} ${bgColor} p-3`}>
      <div className={`text-xs font-semibold uppercase tracking-wide ${labelColor} mb-1.5`}>{label}</div>
      <div className="text-xs text-slate-800 whitespace-pre-wrap leading-relaxed">{text || <span className="italic text-slate-400">(none)</span>}</div>
    </div>
  );
}

function ThresholdsTable({ thresholds }: { thresholds: Record<string, number> }) {
  const labels: Record<string, string> = {
    annual_turnover_min_inr_cr: "Min annual turnover (₹ Cr)",
    annual_turnover_lookback_years: "Turnover lookback (years)",
    similar_work_min_inr_cr: "Min similar-work value (₹ Cr)",
    similar_work_lookback_years: "Similar-work lookback (years)",
    specialized_breakwater_rmt_min: "Min breakwater (Rmt)",
    specialized_dredging_cum_min: "Min dredging (Cum)",
    specialized_piling_diameter_mm_min: "Min piling diameter (mm)",
    specialized_piling_length_rmt_min: "Min piling length (Rmt)",
    solvency_min_inr_cr: "Min solvency (₹ Cr)",
    solvency_max_age_months: "Max solvency cert age (months)",
    emd_validity_min_days: "Min EMD validity (days)",
    performance_security_pct: "Performance security (%)",
    performance_security_dlp_buffer_days: "PBG buffer past DLP (days)",
  };
  return (
    <div>
      <div className="text-xs font-semibold uppercase tracking-wide text-slate-500 mb-1.5">Qualification Thresholds</div>
      <div className="rounded-lg border border-slate-200 divide-y divide-slate-100">
        {Object.entries(thresholds).map(([k, v]) => (
          <div key={k} className="flex items-center justify-between px-3 py-1.5 text-xs">
            <span className="text-slate-700">{labels[k] ?? k}</span>
            <span className="font-mono font-semibold text-slate-900 tabular-nums">{v.toLocaleString()}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
