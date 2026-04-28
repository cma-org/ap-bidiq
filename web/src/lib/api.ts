const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    cache: "no-store",
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`API ${res.status} ${path}: ${text}`);
  }
  return res.json() as Promise<T>;
}

export const apiBase = BASE;

// ---- Types ---------------------------------------------------------------

export type TenderListItem = {
  id: number;
  title: string;
  department: string;
  code: string | null;
  created_at: string;
  section_count: number;
  corrigendum_count: number;
};

export type TenderDetail = {
  id: number;
  title: string;
  department: string;
  code: string | null;
  created_at: string;
  sections: { id: number; name: string; order_idx: number; char_count: number }[];
  corrigenda: { id: number; name: string; order_idx: number }[];
  mandatory_clauses_count: number;
  forms_required_count: number;
};

export type ActiveRules = {
  tender_id: number;
  version: number;
  generated_at: string;
  payload: Record<string, unknown> & {
    thresholds?: Record<string, number>;
    bid_capacity_formula?: Record<string, unknown>;
    extras_protocol?: Record<string, unknown> | null;
  };
};

export type CorrigendumDiff = {
  tender_id: number;
  corrigenda: {
    corrigendum_id: number;
    name: string;
    patches: {
      target_clause: string;
      op: string;
      before: string | null;
      after: string | null;
      summary: string | null;
    }[];
  }[];
};

export type MandatoryClauseRow = {
  id: number;
  code: string;
  title: string;
  source_section: string;
  layer: string;
  source_text_preview: string;
};

export type FormRequiredRow = {
  id: number;
  form_no: string;
  title: string;
  schema: Record<string, string>;
};

export type BidListItem = {
  id: number;
  tender_id: number;
  vendor_name: string;
  jv_partners: string[];
  bid_value_inr: number | null;
  submitted_at: string;
  extraction_count: number;
};

export type ValidationFinding = {
  id: number;
  check_id: string;
  layer: string;
  verdict: "pass" | "fail" | "warning";
  severity: string;
  title: string;
  message: string;
  citation: { section: string | null; clause: string | null; text: string | null };
  evidence: Record<string, unknown>;
};

export type ValidationsResponse = {
  bid_id: number;
  summary: { pass: number; fail: number; warning: number };
  findings: ValidationFinding[];
};

export type EvalStatementResponse = {
  bid_id: number;
  verdict: "qualified" | "not_qualified" | "conditional";
  summary: string | null;
  reasons: { check_id: string; title: string; message: string }[];
  generated_at: string;
  json_payload: {
    rows: {
      check_id: string;
      criterion: string;
      required: string;
      submitted: string;
      meets: boolean;
      verdict: "pass" | "fail" | "warning";
      remarks: string;
      citation: { section: string | null; clause: string | null; text: string | null };
    }[];
    active_rules_version: number;
  };
};

export type BenchmarkResponse = {
  bid_count: number;
  defect_detection_rate: number;
  verdict_match_rate: number;
  false_positive_count: number;
  rows: {
    bid_id: number;
    vendor_name: string;
    expected_verdict: string;
    actual_verdict: string;
    verdict_match: boolean;
    expected_findings: string[];
    caught_findings: string[];
    missed_findings: string[];
    false_positives: string[];
  }[];
};

export type AuditRow = {
  id: number;
  ts: string;
  actor: string;
  action: string;
  payload: Record<string, unknown>;
  prev_hash: string | null;
  this_hash: string;
  note: string | null;
};
