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
    """Classify claim with explicit numeric-comparison layer before final status."""
    if not results:
        return (
            "False",
            "No search evidence found (check API key or internet access).",
            "",
        )

    trusted_results = [r for r in results if _is_trusted(r.get("link", ""))]
    if not trusted_results:
        first_result = results[0]
        return (
            "False",
            _build_correct_information(first_result, "False"),
            first_result.get("link", ""),
        )

    claim_numbers = set(_extract_numbers(claim))
    claim_keywords = _normalize_keywords(claim)

    best_related_result: Optional[Dict[str, str]] = None

    for result in trusted_results:
        evidence_text = f"{result.get('title', '')} {result.get('snippet', '')}"
        evidence_numbers = set(_extract_numbers(evidence_text))
        evidence_keywords = _normalize_keywords(evidence_text)

        overlap_count = len(claim_keywords.intersection(evidence_keywords))
        same_topic = overlap_count >= 2

        if claim_numbers and evidence_numbers and claim_numbers == evidence_numbers:
            return (
                "Verified",
                _build_correct_information(result, "Verified"),
                result.get("link", ""),
            )

        if same_topic:
            best_related_result = result

    if best_related_result is not None:
        return (
            "Inaccurate",
            _build_correct_information(best_related_result, "Inaccurate"),
            best_related_result.get("link", ""),
        )

    fallback = trusted_results[0]
    return (
        "False",
        _build_correct_information(fallback, "False"),
        fallback.get("link", ""),
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