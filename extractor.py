"""PDF extraction and claim-detection helpers."""

from __future__ import annotations

import io
import re
from typing import Iterable, List

import pdfplumber

# ---------------------------------------------------------------------------
# Numeric patterns that are strong signals of a factual/statistical claim.
# ---------------------------------------------------------------------------
NUMERIC_CLAIM_PATTERNS = [
    re.compile(r"\b\d{1,3}(?:,\d{3})*(?:\.\d+)?%\b"),                         # percentages: 32%
    re.compile(r"[$₹€£]\s?\d+(?:,\d{3})*(?:\.\d+)?\b"),                       # currencies: $50 billion
    re.compile(r"\b(19|20)\d{2}\b"),                                            # years: 2024
    re.compile(r"\b\d+(?:\.\d+)?\s?(million|billion|trillion)\b", re.I),       # magnitudes
    re.compile(r"\bQ[1-4]\b", re.I),                                            # quarters: Q1/Q2
    re.compile(r"\b\d+(?:\.\d+)?\s?(km|kg|gb|tb|mhz|ghz|mw|kw)\b", re.I),    # units
    re.compile(r"\b\d{1,2}\s?(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s?\d{2,4}\b", re.I),
]

# ---------------------------------------------------------------------------
# Keyword signals that identify non-numeric factual claims.
# e.g. "The Eiffel Tower is located in Berlin."
# ---------------------------------------------------------------------------
FACTUAL_KEYWORD_PATTERNS = [
    re.compile(r"\b(is|are|was|were)\s+(located|situated|found|based|known|called|named|built|made|invented|discovered|founded|created|established)\b", re.I),
    re.compile(r"\b(capital|largest|smallest|highest|lowest|first|last|only|oldest|newest)\b", re.I),
    re.compile(r"\b(visible|invisible|possible|impossible|true|false|myth|fact)\b", re.I),
    re.compile(r"\b(never|always|only|all|none|every)\b", re.I),
    re.compile(r"\b(humans?|animals?|plants?|species|mammals?|reptiles?|birds?)\b", re.I),
    re.compile(r"\b(named after|part of|type of|kind of|form of|made of|composed of)\b", re.I),
]

# Minimum character length for a sentence to be considered a claim.
MIN_SENTENCE_LENGTH = 20
MIN_WORD_COUNT = 4


# ---------------------------------------------------------------------------
# PDF helpers
# ---------------------------------------------------------------------------

def extract_text_lines_from_pdf(pdf_file: io.BytesIO) -> List[str]:
    """Extract full text from every PDF page and return clean non-empty lines."""
    all_lines: List[str] = []

    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            page_lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
            all_lines.extend(page_lines)

    return all_lines


def _split_into_sentences(lines: Iterable[str]) -> List[str]:
    """
    Join all lines into a single block of text, then split on sentence boundaries.
    This handles PDFs where a paragraph of multiple sentences appears on one line,
    as well as line-wrapped text where a single sentence spans multiple lines.
    """
    full_text = " ".join(lines)
    # Split on '. ', '! ', '? ' followed by a capital letter, or end of string.
    raw_sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', full_text)
    sentences: List[str] = []
    for s in raw_sentences:
        s = s.strip()
        if s:
            sentences.append(s)
    return sentences


# ---------------------------------------------------------------------------
# Claim detection
# ---------------------------------------------------------------------------

def _is_meaningful_sentence(sentence: str) -> bool:
    """Return True if the sentence is long enough to be a real claim."""
    if len(sentence) < MIN_SENTENCE_LENGTH:
        return False
    if len(sentence.split()) < MIN_WORD_COUNT:
        return False
    # Skip heading-like all-caps lines without punctuation.
    if sentence.isupper() and not re.search(r"[.,:;%$₹€£]", sentence):
        return False
    return True


def _has_claim_signal(sentence: str) -> bool:
    """Return True if the sentence contains a numeric OR a factual keyword signal."""
    for pattern in NUMERIC_CLAIM_PATTERNS:
        if pattern.search(sentence):
            return True
    for pattern in FACTUAL_KEYWORD_PATTERNS:
        if pattern.search(sentence):
            return True
    return False


def detect_factual_claims(lines: Iterable[str]) -> List[str]:
    """
    Split lines into individual sentences, then return unique sentences that
    look like factual or statistical claims (numeric OR non-numeric).
    """
    sentences = _split_into_sentences(lines)
    claims: List[str] = []
    seen: set = set()

    for raw_sentence in sentences:
        sentence = " ".join(raw_sentence.split())
        if not _is_meaningful_sentence(sentence):
            continue
        if not _has_claim_signal(sentence):
            continue
        if sentence not in seen:
            seen.add(sentence)
            claims.append(sentence)

    return claims