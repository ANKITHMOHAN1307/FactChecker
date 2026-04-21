"""Claim verification logic using SerpAPI + better comparison rules."""

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
    "macrotrends.net",
    "finance.yahoo.com",
    "annualreports.com",
    "ourworldindata.org",
    "wikipedia.org",
]

# Common years ignored for business-value comparison only
IGNORE_COMMON_YEARS = {"2023", "2024", "2025", "2026"}

# Historical claim words → year matching logic
YEAR_BASED_KEYWORDS = [
    "founded",
    "created",
    "launched",
    "established",
    "started",
    "began",
]

# Business/statistical claims → strict numeric comparison
STRICT_VALUE_KEYWORDS = [
    "revenue",
    "inflation",
    "gdp",
    "population",
    "temperature",
    "profit",
    "worth",
    "valuation",
    "market cap",
]


def _extract_numbers(text: str) -> List[str]:
    """
    Extract all numbers from text
    Example:
    'Founded on Sep 4, 1998' -> ['4', '1998']
    """
    return re.findall(r"\d+\.?\d*", text)


def _is_trusted(url: str) -> bool:
    """
    Check if source is trusted
    """
    return any(domain in url for domain in TRUSTED_DOMAINS)


def _is_year_based_claim(claim: str) -> bool:
    """
    Detect historical claims like:
    founded, created, launched
    """
    claim_lower = claim.lower()
    return any(word in claim_lower for word in YEAR_BASED_KEYWORDS)


def _is_strict_value_claim(claim: str) -> bool:
    """
    Detect business/statistical claims
    """
    claim_lower = claim.lower()
    return any(word in claim_lower for word in STRICT_VALUE_KEYWORDS)


def search_claim(claim: str, api_key: Optional[str]) -> List[Dict[str, str]]:
    """
    Search claim using SerpAPI
    """
    if not api_key:
        return []

    params = {
        "engine": "google",
        "q": claim,
        "api_key": api_key,
        "num": 5,
    }

    try:
        response = requests.get(
            SERPAPI_ENDPOINT,
            params=params,
            timeout=20,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("organic_results", [])

    except requests.RequestException:
        return []


def classify_claim(
    claim: str,
    results: List[Dict[str, str]],
) -> Optional[Tuple[str, str, str]]:
    """
    Smart verification logic

    RULES:

    1. No trusted source -> skip output

    2. Historical claims:
       Example:
       Google founded in 1998

       If year exists in source:
       -> Verified

    3. Revenue/statistical claims:
       Example:
       Apple revenue = 50B

       Need strong numeric match:
       -> Verified

       Wrong values:
       -> Inaccurate
    """

    if not results:
        return None

    trusted_results = [
        r for r in results
        if _is_trusted(r.get("link", ""))
    ]

    if not trusted_results:
        return None

    claim_numbers = set(_extract_numbers(claim))

    if not claim_numbers:
        return None

    is_year_claim = _is_year_based_claim(claim)
    is_value_claim = _is_strict_value_claim(claim)

    best_fallback = trusted_results[0]

    for result in trusted_results:
        source_text = (
            result.get("title", "") + " " +
            result.get("snippet", "")
        )

        source_numbers = set(_extract_numbers(source_text))

        # --------------------------------
        # CASE 1: Historical Year Claims
        # Example: founded in 1998
        # --------------------------------
        if is_year_claim:
            # if any claim year exists in source
            if claim_numbers.intersection(source_numbers):
                return (
                    "Verified",
                    "Historical year matches trusted source.",
                    result.get("link", "")
                )

        # --------------------------------
        # CASE 2: Business Value Claims
        # Example: revenue, GDP, inflation
        # --------------------------------
        elif is_value_claim:
            important_claim_numbers = {
                n for n in claim_numbers
                if n not in IGNORE_COMMON_YEARS
            }

            important_source_numbers = {
                n for n in source_numbers
                if n not in IGNORE_COMMON_YEARS
            }

            # exact important number match
            if (
                important_claim_numbers
                and important_claim_numbers.intersection(
                    important_source_numbers
                )
            ):
                return (
                    "Verified",
                    "Claim matches trusted source values.",
                    result.get("link", "")
                )

        best_fallback = result

    # --------------------------------
    # If trusted source exists
    # but values differ
    # --------------------------------
    return (
        "Inaccurate",
        "Claim does not match trusted source data.",
        best_fallback.get("link", "")
    )


def verify_claims(claims: List[str]) -> List[Dict[str, str]]:
    """
    Verify all claims
    Return rows for Streamlit table
    """

    api_key = os.getenv("SERPAPI_API_KEY", "")
    rows: List[Dict[str, str]] = []

    for claim in claims:
        results = search_claim(
            claim,
            api_key=api_key,
        )

        classified = classify_claim(
            claim,
            results,
        )

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