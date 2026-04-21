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
]



def _extract_numbers(text: str) -> List[str]:
    """Extract normalized numeric tokens for lightweight comparison."""
    raw_nums = re.findall(r"[$₹€£]?\d+(?:,\d{3})*(?:\.\d+)?%?", text)
    return [num.replace(",", "").strip() for num in raw_nums]



def _is_trusted(url: str) -> bool:
    return any(domain in url for domain in TRUSTED_DOMAINS)



def search_claim(claim: str, api_key: Optional[str]) -> List[Dict[str, str]]:
    """Run a live Google search through SerpAPI using the full claim sentence."""
    if not api_key:
        return []

    params = {
        "engine": "google",
        "q": claim,  # full claim, not isolated numbers
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
    """Classify claim with simple explainable rules."""
    if not results:
        return (
            "False",
            "No search evidence found (check API key or internet access).",
            "",
        )

    trusted_results = [r for r in results if _is_trusted(r.get("link", ""))]
    if not trusted_results:
        return (
            "False",
            "No trusted-source result found for this claim.",
            results[0].get("link", ""),
        )

    claim_numbers = set(_extract_numbers(claim))

    for result in trusted_results:
        evidence_text = f"{result.get('title', '')} {result.get('snippet', '')}"
        evidence_numbers = set(_extract_numbers(evidence_text))

        if claim_numbers and claim_numbers.intersection(evidence_numbers):
            return (
                "Verified",
                result.get("snippet", "Trusted source supports this claim."),
                result.get("link", ""),
            )

    # Trusted results exist, but the numbers do not align exactly.
    best = trusted_results[0]
    return (
        "Inaccurate",
        best.get("snippet", "Related evidence exists, but values appear updated/different."),
        best.get("link", ""),
    )



def verify_claims(claims: List[str]) -> List[Dict[str, str]]:
    """Verify all claims one-by-one and prepare output rows for the UI table."""
    api_key = os.getenv("SERPAPI_API_KEY", "")
    rows: List[Dict[str, str]] = []

    for claim in claims:
        results = search_claim(claim, api_key=api_key)
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
