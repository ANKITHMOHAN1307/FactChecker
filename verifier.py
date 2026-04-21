"""Claim verification logic using SerpAPI web search results."""

from __future__ import annotations

import os
import re
from typing import Dict, List, Optional, Tuple

import requests

SERPAPI_ENDPOINT = "https://serpapi.com/search.json"

# Trusted domains only
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
    "macrotrends.net",
    "finance.yahoo.com",
    "annualreports.com",
    "ourworldindata.org",
]

# Ignore common years so 2024 alone does not make something Verified
IGNORE_NUMBERS = {"2023", "2024", "2025", "2026"}


def _extract_numbers(text: str) -> List[str]:
    """Extract numbers like years, percentages, money values."""
    return re.findall(r"\d+\.?\d*", text)


def _is_trusted(url: str) -> bool:
    """Check if the source belongs to a trusted domain."""
    return any(domain in url for domain in TRUSTED_DOMAINS)


def search_claim(claim: str, api_key: Optional[str]) -> List[Dict[str, str]]:
    """Search the full claim using SerpAPI."""
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


def classify_claim(claim: str, results: List[Dict[str, str]]) -> Optional[Tuple[str, str, str]]:
    """
    Classification logic

    Rules:
    1. No trusted source -> do not show output
    2. Ignore common years like 2024
    3. Verified only if important numbers match strongly
    4. If one source is inaccurate but another trusted source verifies correctly,
       return Verified
    5. Only return Inaccurate if no trusted source verifies the claim
    """

    if not results:
        return None

    trusted_results = [
        r for r in results
        if _is_trusted(r.get("link", ""))
    ]

    if not trusted_results:
        return None

    # Important numbers only
    claim_numbers = {
        n for n in _extract_numbers(claim)
        if n not in IGNORE_NUMBERS
    }

    # If no useful numeric value exists, skip weak checking
    if not claim_numbers:
        return None

    best_fallback = trusted_results[0]

    # Check ALL trusted results first
    for result in trusted_results:
        source_text = (
            result.get("title", "") + " " +
            result.get("snippet", "")
        )

        source_numbers = {
            n for n in _extract_numbers(source_text)
            if n not in IGNORE_NUMBERS
        }

        # Strong verification: exact match
        if claim_numbers == source_numbers:
            return (
                "Verified",
                "Claim matches trusted source data.",
                result.get("link", "")
            )

        # Good verification: at least one strong value matches
        if claim_numbers.intersection(source_numbers):
            return (
                "Verified",
                "Claim is supported by trusted source.",
                result.get("link", "")
            )

        best_fallback = result

    # Only after checking all trusted results
    return (
        "Inaccurate",
        "Claim does not match trusted source values.",
        best_fallback.get("link", "")
    )


def verify_claims(claims: List[str]) -> List[Dict[str, str]]:
    """Verify all claims and return rows for Streamlit table."""

    api_key = os.getenv("SERPAPI_API_KEY", "")
    rows: List[Dict[str, str]] = []

    for claim in claims:
        results = search_claim(claim, api_key)
        classified = classify_claim(claim, results)

        # Skip if no useful verification found
        if not classified:
            continue

        status, correct_information, source_link = classified

        rows.append(
            {
                "claim": claim,
                "status": status,
                "correct_information": correct_information,
                "source_link": source_link,
            }
        )

    return rows
