import io
import re

import pdfplumber
import requests

TIMEOUT = 30
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; VislRecruit/1.0)"}


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

    if not content[:4] == b"%PDF":
        # Google Drive virus-scan interstitial returns HTML
        if b"text/html" in resp.headers.get("Content-Type", "").encode() or content[:15].lower().startswith(b"<!doctype"):
            raise ValueError("Could not download PDF (link may require manual access)")
        raise ValueError("File is not a PDF")

    return content


def extract_text(pdf_bytes: bytes) -> str:
    pages = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
    return "\n\n".join(pages).strip()


def process_candidate_resume(candidate: dict) -> dict:
    """Download and parse resume; enrich candidate dict in place."""
    resume_url = candidate.get("resume", "NA")
    na_fields = candidate.get("na_fields", [])

    if resume_url == "NA" or "resume" in na_fields:
        candidate["resume_text"] = "NA"
        candidate["resume_status"] = "na"
        return candidate

    try:
        pdf_bytes = download_resume(resume_url)
        text = extract_text(pdf_bytes)
        if not text:
            candidate["resume_text"] = "NA"
            candidate["resume_status"] = "failed"
            candidate["resume_error"] = "PDF contained no extractable text"
        else:
            candidate["resume_text"] = text
            candidate["resume_status"] = "ok"
            candidate.pop("resume_error", None)
    except Exception as exc:
        candidate["resume_text"] = "NA"
        candidate["resume_status"] = "failed"
        candidate["resume_error"] = str(exc)

    return candidate
