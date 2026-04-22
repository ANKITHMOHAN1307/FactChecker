# extractor.py

from __future__ import annotations

import io
from typing import List

import pdfplumber


def extract_text_lines_from_pdf(pdf_file: io.BytesIO) -> List[str]:
    """
    Extract text and split into one claim per sentence
    """

    claims = []

    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""

            # join lines first
            text = " ".join(
                line.strip()
                for line in text.split("\n")
                if line.strip()
            )

            # simple sentence split
            sentences = text.split(".")

            for sentence in sentences:
                sentence = sentence.strip()

                if len(sentence) < 10:
                    continue

                if sentence.isupper():
                    continue

                # add back period
                sentence = sentence + "."

                claims.append(sentence)

    return claims


def detect_factual_claims(lines: List[str]) -> List[str]:
    """
    Keep all meaningful claims
    No unnecessary filtering
    """

    unique_claims = []
    seen = set()

    for line in lines:
        if line not in seen:
            seen.add(line)
            unique_claims.append(line)

    return unique_claims