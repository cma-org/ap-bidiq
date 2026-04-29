"""OCR pre-processor for scanned PDFs.

Strategy:
1. Try direct text extraction via pypdf — works for text-layer PDFs.
2. If extracted text is too short (likely a scan), shell out to `tesseract`
   via pdf2image + pytesseract.
3. Return both the extracted text and a confidence/method label.

Tesseract + pdftoppm (poppler) are needed in the container. Both are tiny
and apt-installable. For multi-language support we configure Tesseract with
'eng+tel' language packs (Telugu support is on the roadmap).

For v1 demo we degrade gracefully: if Tesseract isn't installed, we return
the direct extraction with a warning. The toggle in the UI lets the officer
opt-in to OCR.
"""
from __future__ import annotations

import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader


@dataclass
class OCRResult:
    text: str
    method: str           # "text-layer" | "tesseract" | "tesseract-fallback"
    page_count: int
    char_count: int
    languages: list[str]  # languages OCR was run with
    note: str = ""


def _direct_text(path: Path) -> str:
    try:
        r = PdfReader(str(path))
        parts = [(p.extract_text() or "") for p in r.pages]
        return "\n".join(parts)
    except Exception:
        return ""


def _tesseract_available() -> bool:
    return shutil.which("tesseract") is not None


def _tesseract_extract(path: Path, languages: list[str]) -> str:
    """Convert PDF pages to images via pdftoppm and OCR each via tesseract.
    Requires poppler-utils + tesseract to be installed.
    """
    out_chunks: list[str] = []
    with tempfile.TemporaryDirectory() as tmp_dir:
        prefix = Path(tmp_dir) / "page"
        # 200 DPI is a good balance for procurement docs
        subprocess.run(
            ["pdftoppm", "-r", "200", "-png", str(path), str(prefix)],
            check=True, capture_output=True,
        )
        page_images = sorted(Path(tmp_dir).glob("page-*.png"))
        lang_arg = "+".join(languages) if languages else "eng"
        for img in page_images:
            res = subprocess.run(
                ["tesseract", str(img), "-", "-l", lang_arg, "--psm", "3"],
                check=True, capture_output=True, text=True,
            )
            out_chunks.append(res.stdout)
    return "\n\n".join(out_chunks)


def extract_pdf(path: Path, *, force_ocr: bool = False, languages: list[str] | None = None) -> OCRResult:
    """Best-effort PDF text extraction with optional OCR fallback / forcing."""
    languages = languages or ["eng"]

    direct = _direct_text(path)
    page_count = 0
    try:
        page_count = len(PdfReader(str(path)).pages)
    except Exception:
        pass

    # Heuristic for "this is a scan": <30 chars per page after direct extraction
    avg_chars = (len(direct) / max(page_count, 1)) if page_count else 0
    looks_scanned = avg_chars < 30 if page_count else False

    if not force_ocr and not looks_scanned and direct:
        return OCRResult(
            text=direct, method="text-layer", page_count=page_count,
            char_count=len(direct), languages=["n/a"],
            note="PDF has a text layer — OCR not needed.",
        )

    if not _tesseract_available():
        return OCRResult(
            text=direct, method="tesseract-fallback",
            page_count=page_count, char_count=len(direct), languages=languages,
            note=("Tesseract not installed in this environment. "
                  "In production, the container image bundles tesseract + poppler."),
        )

    try:
        ocr_text = _tesseract_extract(path, languages)
        return OCRResult(
            text=ocr_text, method="tesseract",
            page_count=page_count, char_count=len(ocr_text), languages=languages,
            note=f"OCR completed via Tesseract with languages: {', '.join(languages)}",
        )
    except Exception as e:
        return OCRResult(
            text=direct, method="tesseract-fallback",
            page_count=page_count, char_count=len(direct), languages=languages,
            note=f"OCR failed: {e}. Returning direct extraction.",
        )
