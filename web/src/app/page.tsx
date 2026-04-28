import Link from "next/link";
import { api, type TenderListItem } from "@/lib/api";
import { Shell, PageHeader } from "@/components/Shell";
import { Card } from "@/components/Card";
import { Badge } from "@/components/Badge";
import { fmtDateOnly } from "@/lib/format";

export default async function Home() {
  let tenders: TenderListItem[] = [];
  let apiError: string | null = null;
  try {
    tenders = await api<TenderListItem[]>("/tenders");
  } catch (e) {
    apiError = e instanceof Error ? e.message : String(e);
  }

  return (
    <Shell>
      <PageHeader
        title="Tenders"
        subtitle="Tender packages ingested into AP-BidIQ. Click a tender to view active rules, corrigenda, and submitted bids."
      />

      {apiError && (
        <Card className="mb-6 border-red-200 bg-red-50">
          <div className="text-sm text-red-800">
            <strong>API not reachable.</strong> Start the FastAPI server: <code className="font-mono text-xs bg-white px-1.5 py-0.5 rounded">cd api && .venv/bin/uvicorn app.main:app --reload</code>
            <div className="mt-1 text-red-600 text-xs">{apiError}</div>
          </div>
        </Card>
      )}

      {!apiError && tenders.length === 0 && (
        <Card>
          <div className="text-sm text-slate-600">
            No tenders found. Run <code className="font-mono text-xs bg-slate-100 px-1.5 py-0.5 rounded">python -m app.cli ingest</code> in the api folder to load the EPCC corpus.
          </div>
        </Card>
      )}

      <div className="grid gap-4">
        {tenders.map((t) => (
          <Link key={t.id} href={`/tenders/${t.id}`} className="block group">
            <Card className="hover:border-sky-400 hover:shadow-md transition">
              <div className="flex items-start justify-between gap-6">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2 mb-1.5">
                    {t.code && <Badge tone="brand" className="font-mono">{t.code}</Badge>}
                    {t.corrigendum_count > 0 && (
                      <Badge tone="warn">
                        {t.corrigendum_count} corrigend{t.corrigendum_count === 1 ? "um" : "a"} applied
                      </Badge>
                    )}
                  </div>
                  <h3 className="text-base font-semibold text-slate-900 group-hover:text-sky-800">
                    {t.title}
                  </h3>
                  <p className="mt-1 text-sm text-slate-600">{t.department}</p>
                  <div className="mt-3 flex items-center gap-4 text-xs text-slate-500">
                    <span>{t.section_count} sections</span>
                    <span>•</span>
                    <span>Loaded {fmtDateOnly(t.created_at)}</span>
                  </div>
                </div>
                <div className="text-slate-400 group-hover:text-sky-600 transition">→</div>
              </div>
            </Card>
          </Link>
        ))}
      </div>
    </Shell>
  );
}
