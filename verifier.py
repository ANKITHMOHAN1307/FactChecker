"""Claim verification logic using SerpAPI web search results."""

from __future__ import annotations

import os
import re
from typing import Dict, List, Optional, Set, Tuple

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

STOPWORDS = {
    "the",
    "a",
    "an",
    "and",
    "or",
    "of",
    "in",
    "to",
    "for",
    "on",
    "with",
    "by",
    "from",
    "at",
    "is",
    "was",
    "were",
    "be",
    "as",
    "that",
    "this",
    "it",
}



def _extract_numbers(text: str) -> List[str]:
    """Step 1/2: Extract numbers using the requested regex pattern."""
    return re.findall(r"\d+\.?\d*", text)



def _normalize_keywords(text: str) -> Set[str]:
    """Small helper to compare if claim and snippet are about the same topic."""
    words = re.findall(r"[a-zA-Z]{3,}", text.lower())
    return {w for w in words if w not in STOPWORDS}



def _is_trusted(url: str) -> bool:
    return any(domain in url for domain in TRUSTED_DOMAINS)



def _build_correct_information(result: Dict[str, str], status: str) -> str:
    """Create a clearer "Correct Information" message for UI output."""
    title = result.get("title", "").strip()
    snippet = result.get("snippet", "").strip()

    if not title and not snippet:
        return "Trusted source found, but detailed snippet is not available."

    evidence_text = f"{title}. {snippet}".strip()

    if status == "Verified":
        return f"Matched evidence: {evidence_text}"
    if status == "Inaccurate":
        return f"Updated/correct evidence: {evidence_text}"
    return f"Closest evidence found: {evidence_text}"



def search_claim(claim: str, api_key: Optional[str]) -> List[Dict[str, str]]:
    """Run a live Google search through SerpAPI using the full claim sentence."""
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
    Simple classification logic

    Rules:
    1. If no trusted source found → False
    2. If claim numbers match source numbers → Verified
    3. If source exists but numbers do not match → Inaccurate
    """

    # No search results at all
    if not results:
        return (
            "False",
            "No source found for this claim.",
            ""
        )

    # Keep only trusted sources
    trusted_results = [
        r for r in results
        if _is_trusted(r.get("link", ""))
    ]

    # No trusted source found
    if not trusted_results:
        return (
            "False",
            "No trusted source found for this claim.",
            results[0].get("link", "")
        )

    # Take first trusted source only (simple approach)
    result = trusted_results[0]

    # Extract numbers from claim and source
    claim_numbers = set(_extract_numbers(claim))

    source_text = (
        result.get("title", "") + " " +
        result.get("snippet", "")
    )

    source_numbers = set(_extract_numbers(source_text))

    # If numbers match exactly → Verified
    if claim_numbers and claim_numbers == source_numbers:
        return (
            "Verified",
            "Claim matches trusted source data.",
            result.get("link", "")
        )

    # Source exists but values differ → Inaccurate
    return (
        "Inaccurate",
        "Claim does not fully match trusted source data.",
        result.get("link", "")
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