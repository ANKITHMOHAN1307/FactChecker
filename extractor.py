
# extractor.py

"""
Simple PDF text extraction + claim detection
Keeps logic simple and reliable
"""

from __future__ import annotations

import io
import re
from typing import List

import pdfplumber


def extract_text_lines_from_pdf(pdf_file: io.BytesIO) -> List[str]:
    """
    Extract clean lines from uploaded PDF
    """

    lines = []

    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""

            for line in text.split("\n"):
                clean_line = " ".join(line.strip().split())

                if clean_line:
                    lines.append(clean_line)

    return lines


def is_valid_claim(line: str) -> bool:
    """
    Very simple filtering:
    - remove very short lines
    - remove full uppercase headings
    - keep normal factual sentences
    """

    if len(line) < 10:
        return False

    if line.isupper():
        return False

    return True


def detect_factual_claims(lines: List[str]) -> List[str]:
    """
    Return all meaningful factual-looking lines
    No over-filtering
    """

    claims = []
    seen = set()

    for line in lines:
        if not is_valid_claim(line):
            continue

        if line not in seen:
            seen.add(line)
            claims.append(line)

    return claims