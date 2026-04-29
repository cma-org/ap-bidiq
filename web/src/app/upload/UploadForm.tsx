"use client";
import { useState } from "react";
import { apiBase } from "@/lib/api";
import { Card, CardHeader } from "@/components/Card";
import { Badge } from "@/components/Badge";

type ExtractResult = {
  filename: string;
  size_bytes: number;
  method: string;
  page_count: number;
  char_count: number;
  languages: string[];
  note: string;
  text_preview: string;
};

export function UploadForm() {
  const [file, setFile] = useState<File | null>(null);
  const [forceOcr, setForceOcr] = useState(false);
  const [languages, setLanguages] = useState("eng+tel");
  const [result, setResult] = useState<ExtractResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit() {
    if (!file) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const fd = new FormData();
      fd.append("file", file);
      fd.append("force_ocr", forceOcr ? "true" : "false");
      fd.append("languages", languages);
      const res = await fetch(`${apiBase}/upload/extract`, { method: "POST", body: fd });
      if (!res.ok) throw new Error(`API ${res.status}`);
      setResult((await res.json()) as ExtractResult);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="grid lg:grid-cols-2 gap-6">
      <Card>
        <CardHeader title="Upload PDF" subtitle="Native PDFs use the text layer (free + instant). Scanned PDFs trigger Tesseract OCR with English + Telugu language models." />

        <label className="block rounded-lg border-2 border-dashed border-slate-300 hover:border-sky-400 transition cursor-pointer bg-slate-50/50 px-6 py-12 text-center">
          <input
            type="file"
            accept="application/pdf"
            className="hidden"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
          />
          <div className="text-3xl mb-2">📄</div>
          {file ? (
            <div>
              <div className="text-sm font-semibold text-slate-900">{file.name}</div>
              <div className="text-xs text-slate-500 mt-1">{(file.size / 1024).toFixed(1)} KB</div>
            </div>
          ) : (
            <div>
              <div className="text-sm font-medium text-slate-700">Drop PDF here or click to browse</div>
              <div className="text-xs text-slate-500 mt-1">Vendor bids, scanned annexures, supporting docs</div>
            </div>
          )}
        </label>

        <div className="mt-5 space-y-3">
          <label className="flex items-center gap-3 text-sm cursor-pointer">
            <input
              type="checkbox"
              checked={forceOcr}
              onChange={(e) => setForceOcr(e.target.checked)}
              className="h-4 w-4"
            />
            <span>
              <span className="font-medium text-slate-900">Force OCR</span>
              <span className="text-slate-500"> — even if a text layer exists. Useful for low-confidence scans.</span>
            </span>
          </label>

          <div>
            <label className="text-xs font-medium text-slate-700 mb-1 block">OCR languages (Tesseract codes)</label>
            <select
              value={languages}
              onChange={(e) => setLanguages(e.target.value)}
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
            >
              <option value="eng">English only</option>
              <option value="eng+tel">English + Telugu (recommended for AP)</option>
              <option value="tel">Telugu only</option>
            </select>
          </div>
        </div>

        <button
          onClick={submit}
          disabled={!file || loading}
          className="mt-5 w-full rounded-lg bg-sky-700 hover:bg-sky-800 text-white text-sm font-semibold px-4 py-2.5 shadow-sm transition disabled:opacity-60"
        >
          {loading ? "Extracting…" : "Extract text"}
        </button>

        {error && <div className="mt-3 text-sm text-red-700">Error: {error}</div>}
      </Card>

      <Card>
        <CardHeader title="Extraction result" />

        {!result && !loading && (
          <div className="text-sm text-slate-500 py-12 text-center">
            Upload a PDF and click <span className="font-medium text-slate-700">Extract</span>.
          </div>
        )}

        {loading && (
          <div className="text-sm text-slate-500 py-12 text-center">
            <div className="inline-block animate-spin h-6 w-6 border-2 border-sky-600 border-t-transparent rounded-full mb-3" />
            <div>{forceOcr ? "Running OCR (may take 10–30s for scanned PDFs)…" : "Extracting…"}</div>
          </div>
        )}

        {result && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <Stat label="Method" value={<MethodBadge method={result.method} />} />
              <Stat label="Pages" value={result.page_count.toString()} />
              <Stat label="Characters extracted" value={result.char_count.toLocaleString()} />
              <Stat label="Size" value={`${(result.size_bytes / 1024).toFixed(1)} KB`} />
              <Stat label="Languages" value={result.languages.join(", ")} />
              <Stat label="Filename" value={result.filename} mono />
            </div>

            <div className="rounded-lg border-l-4 border-sky-700 bg-sky-50 p-3 text-xs text-sky-900">
              {result.note}
            </div>

            <div>
              <div className="text-xs font-semibold uppercase tracking-wide text-slate-500 mb-1.5">
                Text preview ({result.text_preview.length}/{result.char_count} chars)
              </div>
              <pre className="rounded-lg bg-slate-900 text-slate-100 p-3 text-xs leading-relaxed overflow-x-auto max-h-80 whitespace-pre-wrap">
{result.text_preview || "(empty)"}
              </pre>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
}

function Stat({ label, value, mono }: { label: string; value: React.ReactNode; mono?: boolean }) {
  return (
    <div>
      <div className="text-[10px] uppercase tracking-wide text-slate-500 font-medium">{label}</div>
      <div className={`mt-0.5 text-sm text-slate-900 ${mono ? "font-mono text-xs" : ""}`}>{value}</div>
    </div>
  );
}

function MethodBadge({ method }: { method: string }) {
  if (method === "text-layer") return <Badge tone="pass">Text layer ✓</Badge>;
  if (method === "tesseract") return <Badge tone="brand">OCR (Tesseract)</Badge>;
  return <Badge tone="warn">Fallback</Badge>;
}
