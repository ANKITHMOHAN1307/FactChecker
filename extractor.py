# extractor.py

from __future__ import annotations

import io
import re
from typing import List

import pdfplumber


def extract_text_lines_from_pdf(pdf_file: io.BytesIO) -> List[str]:
    """
    Extract text and safely split into claims
    without breaking decimal values like 2.5
    """

    claims = []

    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""

            # Join lines first
            text = " ".join(
                line.strip()
                for line in text.split("\n")
                if line.strip()
            )

            # Split sentences safely
            sentences = re.split(
                r'(?<!\d)\.(?!\d)',
                text
            )

            for sentence in sentences:
                sentence = sentence.strip()

                if len(sentence) < 10:
                    continue

                if sentence.isupper():
                    continue

                # Remove ugly starting words
                sentence = re.sub(
                    r'^(and|while|but)\s+',
                    '',
                    sentence,
                    flags=re.IGNORECASE
                )

                if not sentence.endswith("."):
                    sentence += "."

                claims.append(sentence)

    return claims


def detect_factual_claims(lines: List[str]) -> List[str]:
    """
    Keep unique meaningful claims
    """

    unique_claims = []
    seen = set()

    for line in lines:
        if line not in seen:
            seen.add(line)
            unique_claims.append(line)

    return unique_claims
    