"use client";
import { useState } from "react";
import { apiBase } from "@/lib/api";
import { Card, CardHeader } from "@/components/Card";
import { Badge } from "@/components/Badge";

type DraftSubsection = {
  heading: string;
  body: string;
  cited_clauses: string[];
};
type ThresholdRow = { label: string; value: string; source: string };
type DraftResult = {
  title: string;
  subsections: DraftSubsection[];
  thresholds_table: ThresholdRow[];
  ai_notes: string;
  model_version: string;
};

const SAMPLE_BRIEFS = [
  {
    project_name: "Krishnapatnam Outer Harbour Phase III",
    department: "Infrastructure & Investment Department, AP",
    project_type: "Marine works (EPCC)",
    budget_inr_cr: 425.0,
    location: "Krishnapatnam, AP",
    duration_years: 3,
    special_requirements: "1.5 km breakwater, 600,000 cum dredging, deep-water piling for container terminal",
  },
  {
    project_name: "Machilipatnam Fishing Harbour Modernization",
    department: "Department of Fisheries, AP",
    project_type: "Fishing harbour upgrade (EPCC)",
    budget_inr_cr: 180.0,
    location: "Machilipatnam, Krishna District, AP",
    duration_years: 2,
    special_requirements: "Approach jetty, fish landing center, ice plant, slipway",
  },
  {
    project_name: "Nagayalanka Coastal Protection Works",
    department: "Water Resources Department, AP",
    project_type: "Coastal infrastructure (EPCC)",
    budget_inr_cr: 95.0,
    location: "Nagayalanka, Krishna District, AP",
    duration_years: 2,
    special_requirements: "Shore protection, sea wall reinforcement, dune restoration",
  },
];

const initialBrief = SAMPLE_BRIEFS[0];

export function DraftForm() {
  const [brief, setBrief] = useState(initialBrief);
  const [result, setResult] = useState<DraftResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function update<K extends keyof typeof initialBrief>(k: K, v: (typeof initialBrief)[K]) {
    setBrief((b) => ({ ...b, [k]: v }));
  }

  async function generate() {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await fetch(`${apiBase}/draft/section-1`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tender_id: 1, brief }),
      });
      if (!res.ok) throw new Error(`API ${res.status}`);
      const data = (await res.json()) as DraftResult;
      setResult(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="grid lg:grid-cols-2 gap-6">
      <Card>
        <CardHeader title="Project brief" subtitle="Try one of the sample projects or fill in your own. The assistant uses the AP clause library + the EPCC tender's structural conventions." />

        <div className="flex flex-wrap gap-2 mb-4">
          {SAMPLE_BRIEFS.map((s) => (
            <button
              key={s.project_name}
              onClick={() => setBrief(s)}
              className="text-xs rounded-full border border-slate-200 bg-slate-50 hover:bg-slate-100 px-3 py-1 transition"
            >
              {s.project_name}
            </button>
          ))}
        </div>

        <div className="space-y-3">
          <Field label="Project name">
            <input className={inputClass} value={brief.project_name} onChange={(e) => update("project_name", e.target.value)} />
          </Field>
          <Field label="Department">
            <input className={inputClass} value={brief.department} onChange={(e) => update("department", e.target.value)} />
          </Field>
          <div className="grid grid-cols-2 gap-3">
            <Field label="Project type">
              <input className={inputClass} value={brief.project_type} onChange={(e) => update("project_type", e.target.value)} />
            </Field>
            <Field label="Budget (₹ Cr)">
              <input className={inputClass} type="number" value={brief.budget_inr_cr} onChange={(e) => update("budget_inr_cr", parseFloat(e.target.value) || 0)} />
            </Field>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <Field label="Location">
              <input className={inputClass} value={brief.location} onChange={(e) => update("location", e.target.value)} />
            </Field>
            <Field label="Duration (years)">
              <input className={inputClass} type="number" value={brief.duration_years} onChange={(e) => update("duration_years", parseInt(e.target.value, 10) || 1)} />
            </Field>
          </div>
          <Field label="Special requirements">
            <textarea className={inputClass + " min-h-[80px]"} value={brief.special_requirements} onChange={(e) => update("special_requirements", e.target.value)} />
          </Field>
        </div>

        <button
          onClick={generate}
          disabled={loading}
          className="mt-5 w-full rounded-lg bg-sky-700 hover:bg-sky-800 text-white text-sm font-semibold px-4 py-2.5 shadow-sm transition disabled:opacity-60"
        >
          {loading ? "Generating draft (10–25 sec)…" : "✨ Generate draft Section 1"}
        </button>

        {error && <div className="mt-3 text-sm text-red-700">Error: {error}</div>}
      </Card>

      <Card>
        <CardHeader
          title="Generated draft"
          subtitle={result ? `Model: ${result.model_version}` : "The assistant's output appears here."}
          action={
            result && (
              <Badge tone="info">{result.subsections.length} sections · {result.thresholds_table.length} thresholds</Badge>
            )
          }
        />

        {!result && !loading && (
          <div className="text-sm text-slate-500 py-12 text-center">
            Pick a sample project, then click <span className="font-medium text-slate-700">Generate</span>.
          </div>
        )}

        {loading && (
          <div className="text-sm text-slate-500 py-12 text-center">
            <div className="inline-block animate-spin h-6 w-6 border-2 border-sky-600 border-t-transparent rounded-full mb-3" />
            <div>Calling Claude Sonnet 4.6…</div>
            <div className="text-xs mt-1">Grounded in {`{15 mandatory clauses + 8 KB Section 1 reference}`}</div>
          </div>
        )}

        {result && (
          <div className="space-y-5">
            <div>
              <div className="text-xs font-semibold uppercase tracking-wide text-slate-500 mb-1.5">Document title</div>
              <div className="text-lg font-semibold text-slate-900">{result.title}</div>
            </div>

            {result.thresholds_table.length > 0 && (
              <div>
                <div className="text-xs font-semibold uppercase tracking-wide text-slate-500 mb-1.5">Computed thresholds</div>
                <div className="rounded-lg border border-slate-200 divide-y divide-slate-100">
                  {result.thresholds_table.map((t, i) => (
                    <div key={i} className="flex items-center justify-between px-3 py-1.5 text-xs">
                      <span className="text-slate-700">{t.label}</span>
                      <div className="text-right">
                        <span className="font-mono font-semibold text-slate-900 tabular-nums">{t.value}</span>
                        <div className="text-[10px] text-slate-500">{t.source}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div>
              <div className="text-xs font-semibold uppercase tracking-wide text-slate-500 mb-1.5">Drafted subsections</div>
              <div className="space-y-3 max-h-[28rem] overflow-y-auto pr-2">
                {result.subsections.map((s, i) => (
                  <div key={i} className="rounded-lg border border-slate-200 bg-white p-3">
                    <div className="flex items-center gap-2 mb-1.5 flex-wrap">
                      <span className="text-sm font-semibold text-slate-900">{s.heading}</span>
                      {s.cited_clauses.map((c) => (
                        <Badge key={c} tone="brand" className="font-mono text-[10px]">{c}</Badge>
                      ))}
                    </div>
                    <p className="text-xs text-slate-700 leading-relaxed whitespace-pre-wrap">{s.body}</p>
                  </div>
                ))}
              </div>
            </div>

            {result.ai_notes && (
              <div className="rounded-lg border-l-4 border-amber-400 bg-amber-50 p-3">
                <div className="text-xs font-semibold uppercase tracking-wide text-amber-900 mb-1">⚠ Officer notes from AI</div>
                <p className="text-xs text-amber-900 leading-relaxed">{result.ai_notes}</p>
              </div>
            )}
          </div>
        )}
      </Card>
    </div>
  );
}

const inputClass = "w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-sky-600 focus:border-sky-600";

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="text-xs font-medium text-slate-700 mb-1 inline-block">{label}</span>
      {children}
    </label>
  );
}
