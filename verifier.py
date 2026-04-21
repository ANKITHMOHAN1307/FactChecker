"""Claim verification logic using SerpAPI web search results."""

from __future__ import annotations

import os
import re
from typing import Dict, List, Optional, Tuple

import requests

SERPAPI_ENDPOINT = "https://serpapi.com/search.json"

# Trusted sources for higher-confidence checks
TRUSTED_DOMAINS = [
    ".gov",
    ".edu",
    "worldbank.org",
    "imf.org",
    "oecd.org",
    "un.org",
    "who.int",
    "reuters.com",
    "bloomberg.com",
    "statista.com",
    "sec.gov",
    "finance.yahoo.com",
    "ourworldindata.org",
]

# Ignore common standalone years to reduce weak matches
IGNORE_NUMBERS = {"2023", "2024", "2025", "2026"}


def _extract_numbers(text: str) -> List[str]:
    """Extract number-like tokens from text."""
    return re.findall(r"\d+\.?\d*", text)


def _is_trusted(url: str) -> bool:
    """Return True when the URL appears to be from a trusted domain."""
    return any(domain in url for domain in TRUSTED_DOMAINS)


def search_claim(claim: str, api_key: Optional[str]) -> List[Dict[str, str]]:
    """Search one claim against live web results via SerpAPI."""
    if not api_key:
        return []

    params = {
        "engine": "google",
        "q": claim,
        "api_key": api_key,
        "num": 5,
    }

    try:
        response = requests.get(SERPAPI_ENDPOINT, params=params, timeout=20)
        response.raise_for_status()
        data = response.json()
        return data.get("organic_results", [])
    except requests.RequestException:
        return []


def classify_claim(claim: str, results: List[Dict[str, str]]) -> Tuple[str, str, str]:
    """
    Return one of:
    - Verified: trusted evidence supports the claim numbers
    - Inaccurate: trusted evidence exists but conflicts
    - False: no credible evidence found
    """

    # No results means no supporting evidence from live search
    if not results:
        return (
            "False",
            "No evidence found in live search results.",
            "",
        )

    trusted_results = [r for r in results if _is_trusted(r.get("link", ""))]

    # If we have results but none are trusted, still treat as no credible evidence
    if not trusted_results:
        first_link = results[0].get("link", "") if results else ""
        return (
            "False",
            "No credible trusted source found for this claim.",
            first_link,
        )

    claim_numbers = {n for n in _extract_numbers(claim) if n not in IGNORE_NUMBERS}

    # For non-numeric claims, require direct phrase support in trusted snippets/titles
    if not claim_numbers:
        claim_words = {w.lower() for w in re.findall(r"[A-Za-z]{4,}", claim)}
        claim_words = {
            w
            for w in claim_words
            if w not in {"that", "with", "from", "this", "have", "were", "will", "been"}
        }

        for result in trusted_results:
            source_text = (result.get("title", "") + " " + result.get("snippet", "")).lower()
            overlap = [w for w in claim_words if w in source_text]
            # Simple threshold so random overlap does not pass
            if claim_words and len(overlap) >= max(2, len(claim_words) // 3):
                return (
                    "Verified",
                    "Trusted source text supports this non-numeric claim.",
                    result.get("link", ""),
                )

        return (
            "Inaccurate",
            "Trusted sources found, but support for this wording is weak.",
            trusted_results[0].get("link", ""),
        )

    # Numeric claims: compare numbers against trusted snippets
    fallback_link = trusted_results[0].get("link", "")

    for result in trusted_results:
        source_text = result.get("title", "") + " " + result.get("snippet", "")
        source_numbers = {n for n in _extract_numbers(source_text) if n not in IGNORE_NUMBERS}

        # Strong match: all important values match
        if claim_numbers == source_numbers and claim_numbers:
            return (
                "Verified",
                "Claim values strongly match trusted source data.",
                result.get("link", ""),
            )

        # Practical match: at least one key value overlaps
        if claim_numbers.intersection(source_numbers):
            return (
                "Verified",
                "Claim is supported by overlapping values in trusted source.",
                result.get("link", ""),
            )

    return (
        "Inaccurate",
        "Trusted sources were found, but the values do not match this claim.",
        fallback_link,
    )


def verify_claims(claims: List[str]) -> List[Dict[str, str]]:
    """Verify all extracted claims and build rows for UI display."""

    api_key = os.getenv("SERPAPI_API_KEY", "")
    rows: List[Dict[str, str]] = []

    for claim in claims:
        # Run live search for each claim sentence
        results = search_claim(claim, api_key)
        status, correct_information, source_link = classify_claim(claim, results)

        rows.append(
            {
                "claim": claim,
                "status": status,
                "correct_information": correct_information,
                "source_link": source_link,
            }
        )

    return rows
