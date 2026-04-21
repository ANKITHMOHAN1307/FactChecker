"""PDF extraction and claim-detection helpers."""

from __future__ import annotations

import io
import re
from typing import Iterable, List

import pdfplumber


# Numeric patterns for measurable claims
CLAIM_PATTERNS = [
    re.compile(r"\b\d{1,3}(?:,\d{3})*(?:\.\d+)?%\b"),  # percentages
    re.compile(r"[$₹€£]\s?\d+(?:,\d{3})*(?:\.\d+)?\b"),  # money
    re.compile(r"\b(19|20)\d{2}\b"),  # years
    re.compile(r"\b\d+(?:\.\d+)?\s?(million|billion|trillion)\b", re.I),
    re.compile(r"\bQ[1-4]\b", re.I),
    re.compile(r"\b\d+(?:\.\d+)?\s?(km|kg|gb|tb|mhz|ghz|mw|kw)\b", re.I),
]


# Simple factual words for non-numeric claims
FACT_WORDS = [
    "is",
    "are",
    "was",
    "were",
    "has",
    "have",
    "can",
    "cannot",
    "never",
    "always",
    "because",
    "mainly",
    "capital",
    "created",
    "founded",
    "visible",
    "located",
    "grow",
    "strikes",
    "memory",
    "mammals",
    "closest",
    "temperature",
]


def extract_text_lines_from_pdf(pdf_file: io.BytesIO) -> List[str]:
    """
    Extract text from PDF and return clean lines
    """
    all_lines: List[str] = []

    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            page_lines = [
                line.strip()
                for line in text.splitlines()
                if line.strip()
            ]
            all_lines.extend(page_lines)

    return all_lines


def is_meaningful_line(line: str) -> bool:
    """
    Remove useless lines like empty text or headings
    """

    # Very short lines are usually noise
    if len(line.strip()) < 8:
        return False

    # Ignore full uppercase headings
    if line.isupper():
        return False

    return True


def detect_factual_claims(lines: Iterable[str]) -> List[str]:
    """
    Detect both:
    1. Numeric/statistical claims
    2. General factual statements
    """

    claims: List[str] = []
    seen = set()

    for raw_line in lines:
        line = " ".join(raw_line.split())

        if not is_meaningful_line(line):
            continue

        # Check numeric claims
        has_number = any(
            pattern.search(line)
            for pattern in CLAIM_PATTERNS
        )

        # Check non-numeric factual claims
        has_fact_word = any(
            word in line.lower()
            for word in FACT_WORDS
        )

        # Accept if either matches
        if has_number or has_fact_word:
            if line not in seen:
                seen.add(line)
                claims.append(line)

    return claims