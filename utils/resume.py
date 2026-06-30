import gc
import io
import os
import re
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

import pdfplumber
import requests

TIMEOUT = 30
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; VislRecruit/1.0)"}
MAX_PDF_BYTES = 5 * 1024 * 1024
MAX_PDF_PAGES = 8
MAX_RESUME_TEXT = 12000
EXTRACT_TIMEOUT = int(os.getenv("RESUME_EXTRACT_TIMEOUT", "45"))


def _drive_direct_url(url: str) -> str:
    """Convert Google Drive share links to direct-download URLs."""
    patterns = [
        r"drive\.google\.com/file/d/([a-zA-Z0-9_-]+)",
        r"drive\.google\.com/open\?id=([a-zA-Z0-9_-]+)",
        r"docs\.google\.com/uc\?.*id=([a-zA-Z0-9_-]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            file_id = match.group(1)
            return f"https://drive.google.com/uc?export=download&id={file_id}"
    return url


def download_resume(url: str) -> bytes:
    if not url or url == "NA":
        raise ValueError("No resume link")

    download_url = _drive_direct_url(url.strip())
    resp = requests.get(download_url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)
    resp.raise_for_status()

    content = resp.content
    if len(content) < 100:
        raise ValueError("Downloaded file is too small or empty")
    if len(content) > MAX_PDF_BYTES:
        raise ValueError("PDF too large (max 5MB)")

    if not content[:4] == b"%PDF":
        if b"text/html" in resp.headers.get("Content-Type", "").encode() or content[:15].lower().startswith(b"<!doctype"):
            raise ValueError("Could not download PDF (link may require manual access)")
        raise ValueError("File is not a PDF")

    return content


def extract_text(pdf_bytes: bytes) -> str:
    pages: list[str] = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages[:MAX_PDF_PAGES]:
            try:
                text = page.extract_text(layout=False) or ""
            except Exception:
                text = ""
            if text.strip():
                pages.append(text.strip())
    return "\n\n".join(pages).strip()


def _download_and_extract(resume_url: str) -> str:
    pdf_bytes = download_resume(resume_url)
    text = extract_text(pdf_bytes)
    gc.collect()
    return text


def process_candidate_resume(candidate: dict) -> dict:
    """Download and parse resume; enrich candidate dict in place."""
    resume_url = candidate.get("resume", "NA")
    na_fields = candidate.get("na_fields", [])

    if resume_url == "NA" or "resume" in na_fields:
        candidate["resume_text"] = "NA"
        candidate["resume_status"] = "na"
        return candidate

    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(_download_and_extract, resume_url)
            text = future.result(timeout=EXTRACT_TIMEOUT)

        if not text:
            candidate["resume_text"] = "NA"
            candidate["resume_status"] = "failed"
            candidate["resume_error"] = "PDF contained no extractable text"
        else:
            if len(text) > MAX_RESUME_TEXT:
                text = text[:MAX_RESUME_TEXT] + "\n\n[... truncated ...]"
            candidate["resume_text"] = text
            candidate["resume_status"] = "ok"
            candidate.pop("resume_error", None)
    except FuturesTimeoutError:
        candidate["resume_text"] = "NA"
        candidate["resume_status"] = "failed"
        candidate["resume_error"] = f"PDF parsing timed out after {EXTRACT_TIMEOUT}s"
    except Exception as exc:
        candidate["resume_text"] = "NA"
        candidate["resume_status"] = "failed"
        candidate["resume_error"] = str(exc)

    return candidate
