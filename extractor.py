"""PDF extraction and claim-detection helpers."""

from __future__ import annotations

import io
import re
from typing import Iterable, List

import pdfplumber

# Regex patterns that identify claim-like numeric statements.
CLAIM_PATTERNS = [
    re.compile(r"\b\d{1,3}(?:,\d{3})*(?:\.\d+)?%\b"),  # percentages like 32%
    re.compile(r"[$₹€£]\s?\d+(?:,\d{3})*(?:\.\d+)?\b"),  # currencies
    re.compile(r"\b(19|20)\d{2}\b"),  # years like 2024
    re.compile(r"\b\d+(?:\.\d+)?\s?(million|billion|trillion)\b", re.I),
    re.compile(r"\bQ[1-4]\b", re.I),  # quarter numbers (Q1/Q2)
    re.compile(r"\b\d+(?:\.\d+)?\s?(km|kg|gb|tb|mhz|ghz|mw|kw)\b", re.I),
    re.compile(r"\b\d{1,2}\s?(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s?\d{2,4}\b", re.I),
]

# Very short, title-like lines are usually noise for this task.
MIN_LINE_LENGTH = 25



def extract_text_lines_from_pdf(pdf_file: io.BytesIO) -> List[str]:
    """Extract text from every PDF page and return clean non-empty lines."""
    all_lines: List[str] = []

    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            page_lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
            all_lines.extend(page_lines)

    return all_lines



def is_meaningful_line(line: str) -> bool:
    """Filter out obvious headings and incomplete fragments."""
    if len(line) < MIN_LINE_LENGTH:
        return False

    # Skip heading-like all-caps lines without punctuation.
    if line.isupper() and not re.search(r"[.,:;%$₹€£]", line):
        return False

    # Skip lines that have too few words.
    if len(line.split()) < 5:
        return False

    return True



def detect_factual_claims(lines: Iterable[str]) -> List[str]:
    """Return unique lines that look like factual/statistical claims."""
    claims: List[str] = []
    seen = set()

    for raw_line in lines:
        line = " ".join(raw_line.split())
        if not is_meaningful_line(line):
            continue

        has_claim_signal = any(pattern.search(line) for pattern in CLAIM_PATTERNS)
        if not has_claim_signal:
            continue

        if line not in seen:
            seen.add(line)
            claims.append(line)

    return claims
