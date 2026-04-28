import { api, type AuditRow } from "@/lib/api";
import { Shell, PageHeader } from "@/components/Shell";
import { Card, CardHeader } from "@/components/Card";
import { Badge } from "@/components/Badge";
import { fmtDate } from "@/lib/format";

export default async function AuditPage() {
  const [rows, verify] = await Promise.all([
    api<AuditRow[]>("/audit"),
    api<{ checked: number; broken_rows: number[]; ok: boolean }>("/audit/verify"),
  ]);

  return (
    <Shell>
      <PageHeader
        title="Audit Log"
        subtitle="Append-only, hash-chained record of every AI evaluation. Tamper-evident — any modification breaks the chain."
        actions={
          verify.ok ? (
            <Badge tone="pass">✓ Chain verified · {verify.checked} entries</Badge>
          ) : (
            <Badge tone="fail">✗ Chain broken · {verify.broken_rows.length} bad rows</Badge>
          )
        }
      />

      <Card padded={false}>
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead className="bg-slate-900 text-slate-100">
              <tr>
                <th className="text-left px-3 py-2 text-xs font-semibold uppercase tracking-wide">Timestamp</th>
                <th className="text-left px-3 py-2 text-xs font-semibold uppercase tracking-wide">Actor</th>
                <th className="text-left px-3 py-2 text-xs font-semibold uppercase tracking-wide">Action</th>
                <th className="text-left px-3 py-2 text-xs font-semibold uppercase tracking-wide">Payload</th>
                <th className="text-left px-3 py-2 text-xs font-semibold uppercase tracking-wide">Hash (truncated)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 bg-white">
              {rows.map((r) => (
                <tr key={r.id}>
                  <td className="px-3 py-2 text-xs text-slate-600 tabular-nums whitespace-nowrap">{fmtDate(r.ts)}</td>
                  <td className="px-3 py-2 text-xs text-slate-700">{r.actor}</td>
                  <td className="px-3 py-2 text-xs">
                    <Badge tone="brand" className="font-mono">{r.action}</Badge>
                  </td>
                  <td className="px-3 py-2 text-xs text-slate-700 max-w-md">
                    <code className="font-mono break-all">{JSON.stringify(r.payload)}</code>
                  </td>
                  <td className="px-3 py-2 text-xs text-slate-500 font-mono">{r.this_hash.slice(0, 12)}…</td>
                </tr>
              ))}
              {rows.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-3 py-8 text-center text-sm text-slate-500">
                    Audit log is empty. Run an evaluation to see entries here.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </Card>
    </Shell>
  );
}
