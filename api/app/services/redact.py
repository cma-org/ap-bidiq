"""PII redaction for vendor data before it leaves the boundary to an LLM.

Strategy: regex-based scrubber that masks vendor names, PAN, GST, contact
details, and signatory names with role-preserving placeholders. The redacted
spans are tracked so we can audit "this many PII tokens were masked before
the Claude call."

This is a pragmatic v1. Production would use a more sophisticated NER model
(spaCy + custom rules) and would extend to phone numbers, addresses, account
numbers, etc.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any


# Patterns are ordered: most specific first.
PAN_RE = re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b")
GST_RE = re.compile(r"\b\d{2}[A-Z]{5}\d{4}[A-Z]\d[A-Z\d]Z[A-Z\d]\b")
PHONE_RE = re.compile(r"\b(?:\+?91[-\s]?)?[6-9]\d{9}\b")
EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
CIN_RE = re.compile(r"\b[LU]\d{5}[A-Z]{2}\d{4}[A-Z]{3}\d{6}\b")  # Companies Act CIN


@dataclass
class RedactionReport:
    redacted_spans: list[dict[str, Any]] = field(default_factory=list)
    counts_by_type: dict[str, int] = field(default_factory=dict)

    @property
    def total(self) -> int:
        return sum(self.counts_by_type.values())


def _redact_pattern(text: str, pattern: re.Pattern, kind: str, placeholder_fmt: str, report: RedactionReport, counter: list[int]) -> str:
    def _sub(m: re.Match) -> str:
        counter[0] += 1
        ph = placeholder_fmt.format(n=counter[0])
        report.redacted_spans.append({"kind": kind, "original": m.group(0), "placeholder": ph})
        report.counts_by_type[kind] = report.counts_by_type.get(kind, 0) + 1
        return ph
    return pattern.sub(_sub, text)


def redact_text(text: str, also_mask_names: list[str] | None = None) -> tuple[str, RedactionReport]:
    """Return (redacted_text, report). Vendor names + signatory names are passed in explicitly."""
    report = RedactionReport()
    counter = [0]

    # Apply structured patterns
    text = _redact_pattern(text, PAN_RE, "PAN", "[PAN_{n}]", report, counter)
    text = _redact_pattern(text, GST_RE, "GST", "[GST_{n}]", report, counter)
    text = _redact_pattern(text, CIN_RE, "CIN", "[CIN_{n}]", report, counter)
    text = _redact_pattern(text, EMAIL_RE, "EMAIL", "[EMAIL_{n}]", report, counter)
    text = _redact_pattern(text, PHONE_RE, "PHONE", "[PHONE_{n}]", report, counter)

    # Mask explicit names — case-insensitive, longest-first to avoid partial replaces
    for name in sorted(set(also_mask_names or []), key=len, reverse=True):
        if not name or len(name) < 3:
            continue
        # Word-boundary, case-insensitive
        pattern = re.compile(rf"\b{re.escape(name)}\b", re.IGNORECASE)
        replaced = []
        def _sub(m, _name=name):
            replaced.append(m.group(0))
            return "[VENDOR_NAME]"
        text = pattern.sub(_sub, text)
        if replaced:
            report.redacted_spans.append({"kind": "VENDOR_NAME", "original": name, "placeholder": "[VENDOR_NAME]", "occurrences": len(replaced)})
            report.counts_by_type["VENDOR_NAME"] = report.counts_by_type.get("VENDOR_NAME", 0) + len(replaced)

    return text, report


def redact_payload(payload: Any, also_mask_names: list[str] | None = None) -> tuple[Any, RedactionReport]:
    """Recursively redact any string values in a JSON-like structure."""
    aggregate = RedactionReport()

    def walk(obj: Any) -> Any:
        if isinstance(obj, str):
            redacted, rpt = redact_text(obj, also_mask_names=also_mask_names)
            for span in rpt.redacted_spans:
                aggregate.redacted_spans.append(span)
            for k, v in rpt.counts_by_type.items():
                aggregate.counts_by_type[k] = aggregate.counts_by_type.get(k, 0) + v
            return redacted
        if isinstance(obj, dict):
            return {k: walk(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [walk(x) for x in obj]
        return obj

    out = walk(payload)
    return out, aggregate


def redact_for_llm_call(payload_dict: dict[str, Any], vendor_names: list[str]) -> tuple[str, RedactionReport]:
    """Convenience: redact a dict + return JSON string ready to pass to LLM. Used by validators."""
    redacted, report = redact_payload(payload_dict, also_mask_names=vendor_names)
    return json.dumps(redacted, indent=2), report
