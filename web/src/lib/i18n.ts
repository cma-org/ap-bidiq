// Lightweight i18n. v1 covers nav + key headings. Production would expand to
// per-route bundles. Telugu translations are AI-assisted; production would
// have a human procurement domain-expert review.

export type Lang = "en" | "te";

export const LANG_NAMES: Record<Lang, string> = {
  en: "English",
  te: "తెలుగు",
};

type Strings = Record<string, string>;

const EN: Strings = {
  brand_name: "AP-BidIQ",
  brand_tagline: "Bid Evaluation for AP Procurement",
  nav_tenders: "Tenders",
  nav_bids: "Bids",
  nav_compare: "Compare",
  nav_benchmark: "Benchmark",
  nav_audit: "Audit",
  nav_drafting: "Draft",
  nav_anomalies: "Anomalies",
  page_tenders_title: "Tenders",
  page_tenders_subtitle:
    "Tender packages ingested into AP-BidIQ. Click a tender to view active rules, corrigenda, and submitted bids.",
  page_bids_title: "Submitted Bids",
  page_compare_title: "Bid Comparison",
  page_benchmark_title: "Accuracy Benchmark",
  page_audit_title: "Audit Log",
  page_drafting_title: "AI Drafting Assistant",
  page_drafting_subtitle:
    "Generate a draft Section 1 (Instructions to Tenderers) for a new project, grounded in the AP clause library.",
  page_anomalies_title: "Cross-Bid Anomalies",
  page_anomalies_subtitle:
    "Pairwise patterns suggesting collusion, copy-paste experience claims, or shared partners.",
  btn_view_bids: "View Bids",
  btn_revaluate: "Re-evaluate all bids",
  btn_export_docx: "Export DOCX",
  btn_view_source: "View source",
  btn_generate: "Generate draft",
  status_qualified: "Qualified",
  status_not_qualified: "Not Qualified",
  status_conditional: "Conditional",
  label_total_checks: "Total checks",
  label_passing: "Passing",
  label_failing: "Failing",
  label_warnings: "Warnings",
  label_corrigendum_diff: "Corrigendum Diff",
  label_active_rules: "Active Rules",
  label_mandatory_clauses: "Mandatory Clauses",
};

const TE: Strings = {
  brand_name: "AP-BidIQ",
  brand_tagline: "AP ప్రొక్యూర్‌మెంట్ కోసం బిడ్ మూల్యాంకనం",
  nav_tenders: "టెండర్లు",
  nav_bids: "బిడ్‌లు",
  nav_compare: "పోల్చు",
  nav_benchmark: "కచ్చితత్వం",
  nav_audit: "ఆడిట్",
  nav_drafting: "డ్రాఫ్ట్",
  nav_anomalies: "అనోమలీలు",
  page_tenders_title: "టెండర్లు",
  page_tenders_subtitle:
    "AP-BidIQలో లోడ్ చేయబడిన టెండర్ పాకేజీలు. క్రియాశీల నిబంధనలు, సవరణలు మరియు సమర్పించిన బిడ్‌లను చూడటానికి టెండర్‌పై క్లిక్ చేయండి.",
  page_bids_title: "సమర్పించిన బిడ్‌లు",
  page_compare_title: "బిడ్ పోలిక",
  page_benchmark_title: "కచ్చితత్వ బెంచ్‌మార్క్",
  page_audit_title: "ఆడిట్ లాగ్",
  page_drafting_title: "AI డ్రాఫ్టింగ్ అసిస్టెంట్",
  page_drafting_subtitle:
    "AP క్లాజ్ లైబ్రరీపై ఆధారపడి కొత్త ప్రాజెక్ట్ కోసం సెక్షన్ 1 (ఇన్‌స్ట్రక్షన్స్ టు టెండరర్స్) ముసాయిదాను రూపొందించండి.",
  page_anomalies_title: "క్రాస్-బిడ్ అనోమలీలు",
  page_anomalies_subtitle:
    "కుట్ర, కాపీ-పేస్ట్ అనుభవం లేదా షేర్డ్ పార్ట్‌నర్‌లను సూచించే నమూనాలు.",
  btn_view_bids: "బిడ్‌లు చూడండి",
  btn_revaluate: "అన్ని బిడ్‌లను తిరిగి మూల్యాంకనం చేయండి",
  btn_export_docx: "DOCX ఎగుమతి",
  btn_view_source: "మూలం చూడండి",
  btn_generate: "ముసాయిదా రూపొందించండి",
  status_qualified: "అర్హత",
  status_not_qualified: "అర్హత లేదు",
  status_conditional: "షరతులతో",
  label_total_checks: "మొత్తం చెక్‌లు",
  label_passing: "ఉత్తీర్ణత",
  label_failing: "విఫలం",
  label_warnings: "హెచ్చరికలు",
  label_corrigendum_diff: "సవరణ తేడా",
  label_active_rules: "క్రియాశీల నిబంధనలు",
  label_mandatory_clauses: "తప్పనిసరి క్లాజ్‌లు",
};

const BUNDLES: Record<Lang, Strings> = { en: EN, te: TE };

export function t(lang: Lang, key: keyof typeof EN): string {
  return BUNDLES[lang][key] ?? EN[key] ?? key;
}
