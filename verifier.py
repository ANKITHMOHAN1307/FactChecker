# verifier.py

"""
Simple fact verification using SerpAPI
No over-complex number matching
Uses source snippet comparison only
"""

from __future__ import annotations

import os
from typing import Dict, List

import requests


SERPAPI_URL = "https://serpapi.com/search.json"

TRUSTED_DOMAINS = [
    "wikipedia.org",
    "britannica.com",
    "worldbank.org",
    "imf.org",
    "who.int",
    "reuters.com",
    "bloomberg.com",
    "statista.com",
    "macrotrends.net",
    "finance.yahoo.com",
    "sec.gov",
    ".gov",
    ".edu",
]


def is_trusted(link: str) -> bool:
    """
    Check trusted source
    """

    return any(domain in link for domain in TRUSTED_DOMAINS)


def search_claim(claim: str, api_key: str) -> List[Dict]:
    """
    Search full claim using SerpAPI
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
            SERPAPI_URL,
            params=params,
            timeout=20,
        )

        response.raise_for_status()

        data = response.json()

        return data.get("organic_results", [])

    except Exception:
        return []


def classify_claim(claim: str, results: List[Dict]):
    """
    Simple rules:

    1. If no trusted source -> skip
    2. If source strongly supports claim -> Verified
    3. Otherwise -> Inaccurate

    Never force false from weak logic
    """

    if not results:
        return None

    trusted_results = []

    for result in results:
        link = result.get("link", "")

        if is_trusted(link):
            trusted_results.append(result)

    if not trusted_results:
        return None

    claim_lower = claim.lower()

    for result in trusted_results:
        title = result.get("title", "").lower()
        snippet = result.get("snippet", "").lower()
        link = result.get("link", "")

        combined_text = title + " " + snippet

        # Strong keyword overlap
        important_words = [
            word for word in claim_lower.split()
            if len(word) > 3
        ]

        match_count = 0

        for word in important_words:
            if word in combined_text:
                match_count += 1

        # Strong enough support
        if match_count >= 3:
            return (
                "Verified",
                result.get("snippet", "Supported by trusted source."),
                link,
            )

    # If trusted source exists but no strong support
    first = trusted_results[0]

    return (
        "Inaccurate",
        first.get("snippet", "Claim does not fully match trusted source."),
        first.get("link", ""),
    )


def verify_claims(claims: List[str]) -> List[Dict]:
    """
    Verify all claims for Streamlit output
    """

    api_key = os.getenv("SERPAPI_API_KEY", "")

    rows = []

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