# extractor.py

from __future__ import annotations

import io
import re
from typing import List

import pdfplumber


def extract_text_lines_from_pdf(pdf_file: io.BytesIO) -> List[str]:
    """
    Extract PDF text and split into proper factual claims
    without breaking decimal numbers like 5.2
    """

    claims = []

    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""

            # Join broken PDF lines
            text = " ".join(
                line.strip()
                for line in text.split("\n")
                if line.strip()
            )

            # Correct sentence split:
            # split on "." unless next char is a digit
            sentences = re.split(r'\.(?!\d)', text)

            for sentence in sentences:
                sentence = sentence.strip()

                if len(sentence) < 10:
                    continue

                if sentence.isupper():
                    continue

                # remove ugly prefixes
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
    Keep only unique claims
    """

    unique_claims = []
    seen = set()

    for line in lines:
        if line not in seen:
            seen.add(line)
            unique_claims.append(line)

    return unique_claims