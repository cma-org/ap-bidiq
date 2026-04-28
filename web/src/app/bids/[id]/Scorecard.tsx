"use client";
import { useState } from "react";
import type { ValidationFinding } from "@/lib/api";
import { Badge } from "@/components/Badge";

export function Scorecard({ findings }: { findings: ValidationFinding[] }) {
  const [open, setOpen] = useState<ValidationFinding | null>(null);
  return (
    <>
      <div className="grid gap-2">
        {findings.map((f) => (
          <button
            key={f.id}
            onClick={() => setOpen(f)}
            className="text-left rounded-lg border border-slate-200 bg-white hover:border-sky-400 hover:shadow-sm transition px-4 py-3 flex items-center gap-4"
          >
            <FindingIcon verdict={f.verdict} />
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-0.5">
                <span className="font-mono text-xs text-slate-500">{f.check_id}</span>
                <Badge tone={f.layer === "L1" ? "brand" : "info"} className="font-mono">{f.layer}</Badge>
              </div>
              <div className="text-sm font-medium text-slate-900">{f.title}</div>
              <div className="text-xs text-slate-600 mt-0.5 line-clamp-2">{f.message}</div>
            </div>
            <div className="text-xs text-sky-700 font-medium shrink-0">View source →</div>
          </button>
        ))}
      </div>

      {open && <CitationDrawer finding={open} onClose={() => setOpen(null)} />}
    </>
  );
}

function FindingIcon({ verdict }: { verdict: "pass" | "fail" | "warning" }) {
  if (verdict === "pass") {
    return <div className="h-7 w-7 rounded-full bg-emerald-100 grid place-items-center text-emerald-700 font-bold shrink-0">✓</div>;
  }
  if (verdict === "fail") {
    return <div className="h-7 w-7 rounded-full bg-red-100 grid place-items-center text-red-700 font-bold shrink-0">✗</div>;
  }
  return <div className="h-7 w-7 rounded-full bg-amber-100 grid place-items-center text-amber-800 font-bold shrink-0">!</div>;
}

function CitationDrawer({ finding, onClose }: { finding: ValidationFinding; onClose: () => void }) {
  const evidence = finding.evidence as Record<string, unknown>;
  return (
    <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-sm flex" onClick={onClose}>
      <div
        className="ml-auto h-full w-full max-w-xl bg-white shadow-2xl overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="sticky top-0 bg-white border-b border-slate-200 px-6 py-4 flex items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <FindingIcon verdict={finding.verdict} />
              <span className="font-mono text-xs text-slate-500">{finding.check_id}</span>
              <Badge tone={finding.layer === "L1" ? "brand" : "info"} className="font-mono">{finding.layer}</Badge>
            </div>
            <h2 className="text-lg font-semibold text-slate-900">{finding.title}</h2>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-700 text-2xl leading-none">×</button>
        </div>

        <div className="px-6 py-5 space-y-6">
          <div>
            <div className="text-xs font-semibold uppercase tracking-wide text-slate-500 mb-1.5">Finding</div>
            <p className="text-sm text-slate-800 leading-relaxed">{finding.message}</p>
          </div>

          {finding.citation.text && (
            <div>
              <div className="text-xs font-semibold uppercase tracking-wide text-slate-500 mb-1.5">
                Source citation
              </div>
              <div className="rounded-lg border-l-4 border-sky-700 bg-sky-50 px-4 py-3">
                <div className="flex items-center gap-2 mb-2">
                  {finding.citation.section && <Badge tone="brand">{finding.citation.section}</Badge>}
                  {finding.citation.clause && <Badge tone="info" className="font-mono">{finding.citation.clause}</Badge>}
                </div>
                <p className="text-sm text-slate-800 leading-relaxed italic">
                  &ldquo;{finding.citation.text}&rdquo;
                </p>
              </div>
            </div>
          )}

          {Object.keys(evidence).length > 0 && (
            <div>
              <div className="text-xs font-semibold uppercase tracking-wide text-slate-500 mb-1.5">Evidence</div>
              <pre className="rounded-lg bg-slate-900 text-slate-100 px-4 py-3 text-xs leading-relaxed overflow-x-auto">
{JSON.stringify(evidence, null, 2)}
              </pre>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
