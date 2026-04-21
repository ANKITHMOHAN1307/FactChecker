"""Claim verification logic using SerpAPI web search results."""

from __future__ import annotations

import os
import re
from typing import Dict, List, Optional, Tuple

import requests

SERPAPI_ENDPOINT = "https://serpapi.com/search.json"
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
    "britannica.com",
    "investopedia.com",
    "forbes.com",
    "macrotrends.net",
    "companiesmarketcap.com",
    "finance.yahoo.com",
    "annualreports.com",
    "tradingeconomics.com",
    "ourworldindata.org",
]


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
    Simple classification logic

    Rules:
    1. No source found -> False
    2. Trusted source + at least one number match -> Verified
    3. Trusted source + numbers differ -> Inaccurate
    """

    # No results at all
    if not results:
        return None

    # Keep only trusted sources
    trusted_results = [
        r for r in results
        if _is_trusted(r.get("link", ""))
    ]

    # No trusted source found
    if not trusted_results:
        return None

    # Check trusted sources one by one
    claim_numbers = ()
    claim_numbers = set(_extract_numbers(claim))

    for result in trusted_results:
        source_text = (
            result.get("title", "") + " " +
            result.get("snippet", "")
        )

        source_numbers = set(_extract_numbers(source_text))

        # Verified only when most important numbers match strongly
        common_numbers = claim_numbers.intersection(source_numbers)

        # Require stronger match: at least 2 matching numbers
        # or exact match when claim has only 1 number
        if claim_numbers:
            if len(claim_numbers) == 1 and common_numbers == claim_numbers:
                return (
                    "Verified",
                    "Claim matches trusted source data.",
                    result.get("link", "")
                )

            if len(common_numbers) >= 2:
                return (
                    "Verified",
                    "Claim matches trusted source data.",
                    result.get("link", "")
                )

    # Trusted source exists but values differ
    first_result = trusted_results[0]
    return (
        "Inaccurate",
        "Claim does not fully match trusted source data.",
        first_result.get("link", "")
    )


def verify_claims(claims: List[str]) -> List[Dict[str, str]]:
    """Verify all claims and return rows for Streamlit table."""
    api_key = os.getenv("SERPAPI_API_KEY", "")
    rows: List[Dict[str, str]] = []

    for claim in claims:
        results = search_claim(claim, api_key)
        classified = classify_claim(claim, results)

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
