# extractor.py

"""
PDF text extraction + claim detection
Joins lines into full paragraphs first, then splits into complete sentences.
Only keeps sentences with numerical signals (numbers, %, $, etc.)
"""

from __future__ import annotations

import io
import re
from typing import List

import pdfplumber


def extract_text_lines_from_pdf(pdf_file: io.BytesIO) -> List[str]:
    """
    Extract all text from PDF and return as a list of full paragraphs.
    Lines are joined per page to preserve sentence continuity.
    """
    paragraphs = []

    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""

            # Join all lines on this page into one continuous block
            joined = " ".join(
                line.strip()
                for line in text.split("\n")
                if line.strip()
            )

            if joined:
                paragraphs.append(joined)

    return paragraphs


def _split_into_sentences(paragraphs: List[str]) -> List[str]:
    """
    Split paragraphs into individual sentences.
    Splits on '. ' or '.' at end of string, followed by a capital letter.
    Handles cases like '5.2%' or '1998.' correctly.
    """
    sentences = []

    for paragraph in paragraphs:
        # Split on period+space followed by an uppercase letter
        # This avoids splitting on decimal numbers like 5.2 or abbreviations
        raw_splits = re.split(r'(?<=[a-zA-Z0-9%])\.\s+(?=[A-Z])', paragraph)

        for part in raw_splits:
            part = part.strip()

            # Re-attach the period if it was stripped during split
            if part and not part.endswith("."):
                part = part + "."

            if part:
                sentences.append(part)

    return sentences


def _has_numerical_signal(sentence: str) -> bool:
    """
    Returns True if sentence contains any of:
    - A standalone number (e.g. 1975, 2024)
    - A percentage (e.g. 5.2%, 15%)
    - A currency symbol (e.g. $50, ₹200, €100)
    - A number with units (e.g. 2.5 billion, 100 km)
    """
    patterns = [
        r'\b\d{4}\b',                                           # years like 1975, 2024
        r'\b\d+(\.\d+)?%',                                      # percentages like 5.2%, 15%
        r'[\$₹€£]\s?\d+',                                       # currencies like $50, ₹200
        r'\b\d+(\.\d+)?\s?(million|billion|trillion|crore)\b',  # large numbers
        r'\b\d{1,3}(,\d{3})+\b',                               # formatted numbers like 1,000
        r'\b\d+(\.\d+)?\s?(km|kg|gb|tb|mw|kw|mph|kph)\b',     # units
    ]

    return any(re.search(p, sentence, re.IGNORECASE) for p in patterns)


def is_valid_claim(sentence: str) -> bool:
    """
    A valid claim must:
    - Be at least 15 characters long
    - Have at least 4 words
    - Not be all uppercase (headings)
    - Contain a numerical signal
    """
    if len(sentence) < 15:
        return False

    if len(sentence.split()) < 4:
        return False

    if sentence.isupper():
        return False

    if not _has_numerical_signal(sentence):
        return False

    return True


def detect_factual_claims(lines: List[str]) -> List[str]:
    """
    Main pipeline:
    1. Split joined paragraphs into full sentences
    2. Filter to only sentences with numerical signals
    3. Deduplicate
    """
    sentences = _split_into_sentences(lines)

    claims = []
    seen = set()

    for sentence in sentences:
        if not is_valid_claim(sentence):
            continue

        if sentence not in seen:
            seen.add(sentence)
            claims.append(sentence)

    return claims