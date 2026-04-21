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
    """Extract plain numeric tokens for lightweight comparison."""
    return re.findall(r"\d+\.?\d*", text)



def _normalize_keywords(text: str) -> Set[str]:
    """Convert text into comparable keywords for same-topic matching."""
    words = re.findall(r"[a-zA-Z]{3,}", text.lower())
    return {w for w in words if w not in STOPWORDS}



def _is_trusted(url: str) -> bool:
    return any(domain in url for domain in TRUSTED_DOMAINS)



def _build_correct_information(result: Dict[str, str], status: str) -> str:
    """Create readable evidence text for the UI."""
    title = result.get("title", "").strip()
    snippet = result.get("snippet", "").strip()
    evidence_text = f"{title}. {snippet}".strip(" .")

    if not evidence_text:
        return "Trusted source found, but snippet details are unavailable."

    if status == "Verified":
        return f"Verified by source: {evidence_text}"
    return f"Source evidence (not enough to verify): {evidence_text}"



def search_claim(claim: str, api_key: Optional[str]) -> List[Dict[str, str]]:
    """Run live Google search via SerpAPI using the full claim sentence."""
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
    """Simple workflow: source+support => Verified, otherwise False."""
    if not results:
        return (
            "False",
            "No source found from live search (check API key/internet).",
            "",
        )

    trusted_results = [r for r in results if _is_trusted(r.get("link", ""))]
    if not trusted_results:
        first = results[0]
        return (
            "False",
            _build_correct_information(first, "False"),
            first.get("link", ""),
        )

    claim_numbers = set(_extract_numbers(claim))
    claim_keywords = _normalize_keywords(claim)

    for result in trusted_results:
        evidence_text = f"{result.get('title', '')} {result.get('snippet', '')}"
        evidence_numbers = set(_extract_numbers(evidence_text))
        evidence_keywords = _normalize_keywords(evidence_text)

        keyword_overlap = len(claim_keywords.intersection(evidence_keywords))
        same_topic = keyword_overlap >= 2

        # If claim has numbers, require same topic + at least one number match.
        if claim_numbers:
            if same_topic and claim_numbers.intersection(evidence_numbers):
                return (
                    "Verified",
                    _build_correct_information(result, "Verified"),
                    result.get("link", ""),
                )
        # If claim has no numbers, same-topic evidence is enough.
        else:
            if same_topic:
                return (
                    "Verified",
                    _build_correct_information(result, "Verified"),
                    result.get("link", ""),
                )

    # Source exists but does not support claim strongly enough.
    fallback = trusted_results[0]
    return (
        "False",
        _build_correct_information(fallback, "False"),
        fallback.get("link", ""),
    )



def verify_claims(claims: List[str]) -> List[Dict[str, str]]:
    """Verify all claims and return rows for the UI table."""
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