"""Upload endpoint: accept a PDF, optionally OCR it, return extracted text + meta."""
from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.services.ocr import extract_pdf

router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("/extract")
async def post_upload_extract(
    file: UploadFile = File(...),
    force_ocr: bool = Form(False),
    languages: str = Form("eng"),
):
    """Accept a PDF, run extraction (with optional OCR), return preview + meta.

    `languages` is a '+' separated tesseract lang code list, e.g. "eng" or "eng+tel".
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only .pdf files supported in this endpoint for v1.")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        contents = await file.read()
        tmp.write(contents)
        tmp_path = Path(tmp.name)

    try:
        lang_list = [s.strip() for s in languages.split("+") if s.strip()]
        result = extract_pdf(tmp_path, force_ocr=force_ocr, languages=lang_list)
    finally:
        try:
            tmp_path.unlink()
        except OSError:
            pass

    return {
        "filename": file.filename,
        "size_bytes": len(contents),
        "method": result.method,
        "page_count": result.page_count,
        "char_count": result.char_count,
        "languages": result.languages,
        "note": result.note,
        "text_preview": result.text[:2000],
    }
