"""Claim verification logic using SerpAPI web search results."""

from __future__ import annotations

import os
import re
from typing import Dict, List, Optional, Set, Tuple

import requests

SERPAPI_ENDPOINT = "https://serpapi.com/search.json"

# Expanded trusted domain list to cover encyclopaedias, fact-checkers, science sites.
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
    # Encyclopaedias & general reference
    "wikipedia.org",
    "britannica.com",
    "britannica.co",
    # Fact-checking sites
    "snopes.com",
    "factcheck.org",
    "politifact.com",
    "fullfact.org",
    # Science & knowledge
    "nasa.gov",
    "nationalgeographic.com",
    "scientificamerican.com",
    "nature.com",
    "science.org",
    "newscientist.com",
    # News
    "bbc.com",
    "bbc.co.uk",
    "apnews.com",
    "theguardian.com",
    "nytimes.com",
    "washingtonpost.com",
    "theatlantic.com",
    "economist.com",
    # Business & finance
    "forbes.com",
    "wsj.com",
    "ft.com",
]

# Phrases in search snippets that strongly signal a claim is a debunked myth.
MYTH_SIGNALS = [
    "myth",
    "misconception",
    "false",
    "not true",
    "debunked",
    "actually",
    "contrary to",
    "no scientific",
    "no evidence",
    "inaccurate",
    "incorrect",
]

STOPWORDS: Set[str] = {
    "the", "a", "an", "and", "or", "of", "in", "to", "for", "on", "with",
    "by", "from", "at", "is", "was", "were", "be", "as", "that", "this",
    "it", "its", "are", "have", "has", "had", "not", "can", "but", "also",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_numbers(text: str) -> List[str]:
    """Extract all numeric tokens (integers and decimals) from text."""
    return re.findall(r"\d+\.?\d*", text)


def _normalize_keywords(text: str) -> Set[str]:
    """Return a set of meaningful lowercase words (≥3 chars, not stopwords)."""
    words = re.findall(r"[a-zA-Z]{3,}", text.lower())
    return {w for w in words if w not in STOPWORDS}


def _is_trusted(url: str) -> bool:
    return any(domain in url for domain in TRUSTED_DOMAINS)


def _snippet_contradicts_claim(claim_keywords: Set[str], evidence_text: str) -> bool:
    """
    Return True if the evidence text contains myth/debunking language AND shares
    enough topic keywords with the claim to be talking about the same thing.
    """
    text_lower = evidence_text.lower()
    has_myth_signal = any(signal in text_lower for signal in MYTH_SIGNALS)
    evidence_keywords = _normalize_keywords(evidence_text)
    topic_overlap = len(claim_keywords.intersection(evidence_keywords))
    return has_myth_signal and topic_overlap >= 2


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

def search_claim(claim: str, api_key: Optional[str]) -> List[Dict[str, str]]:
    """Run a live Google search through SerpAPI for the given claim."""
    if not api_key:
        return []

    params = {
        "engine": "google",
        "q": claim,
        "api_key": api_key,
        "num": 7,           # fetch a few more results to improve coverage
    }

    try:
        response = requests.get(SERPAPI_ENDPOINT, params=params, timeout=20)
        response.raise_for_status()
        data = response.json()
        results = data.get("organic_results", [])

        # Also include "answer box" / "knowledge graph" snippets when present.
        answer_box = data.get("answer_box", {})
        if answer_box:
            synthetic = {
                "title": answer_box.get("title", ""),
                "snippet": answer_box.get("snippet") or answer_box.get("answer", ""),
                "link": answer_box.get("link", "https://www.google.com"),
            }
            if synthetic["snippet"]:
                results = [synthetic] + results

        return results
    except requests.RequestException:
        return []


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------

def classify_claim(claim: str, results: List[Dict[str, str]]) -> Tuple[str, str, str]:
    """
    Classify a single claim as Verified / Inaccurate / False.

    Logic (in priority order):
    1. No results at all → False (API/connectivity issue).
    2. No trusted results → False.
    3. Trusted snippet contains myth/debunking language about this topic → False.
    4. Claim has numbers AND a trusted snippet has exactly the same numbers
       AND they share enough topic keywords → Verified.
    5. Claim has numbers AND a trusted snippet is on the same topic but
       numbers differ → Inaccurate.
    6. Claim has NO numbers AND a trusted snippet on the same topic does NOT
       contain debunking language → Verified (non-numeric factual claim confirmed).
    7. Claim has NO numbers AND no trusted snippet matches the topic → False.
    8. Fallback → False.
    """
    if not results:
        return (
            "False",
            "No search evidence found (check API key or internet access).",
            "",
        )

    trusted_results = [r for r in results if _is_trusted(r.get("link", ""))]
    if not trusted_results:
        # Even if no result is on a trusted domain, use the best available result
        # to report a source, but mark as False because we can't confirm.
        return (
            "False",
            "No trusted-source result found for this claim.",
            results[0].get("link", "") if results else "",
        )

    claim_numbers: Set[str] = set(_extract_numbers(claim))
    claim_keywords: Set[str] = _normalize_keywords(claim)

    best_same_topic_result: Optional[Dict[str, str]] = None
    best_contradicting_result: Optional[Dict[str, str]] = None

    for result in trusted_results:
        evidence_text = f"{result.get('title', '')} {result.get('snippet', '')}"
        evidence_numbers: Set[str] = set(_extract_numbers(evidence_text))
        evidence_keywords: Set[str] = _normalize_keywords(evidence_text)

        topic_overlap = len(claim_keywords.intersection(evidence_keywords))
        same_topic = topic_overlap >= 2

        # --- Check for explicit contradiction / debunking ---
        if _snippet_contradicts_claim(claim_keywords, evidence_text):
            if best_contradicting_result is None:
                best_contradicting_result = result
            continue   # don't use as positive evidence

        if not same_topic:
            continue

        # --- Numeric claim: compare numbers ---
        if claim_numbers:
            if evidence_numbers and claim_numbers == evidence_numbers:
                # Exact number match on same topic → Verified.
                return (
                    "Verified",
                    result.get("snippet", "Trusted source supports this claim."),
                    result.get("link", ""),
                )
            # Numbers differ but same topic → candidate for Inaccurate.
            if best_same_topic_result is None:
                best_same_topic_result = result

        else:
            # --- Non-numeric claim: same topic, no contradiction → Verified ---
            return (
                "Verified",
                result.get("snippet", "Trusted source confirms this claim."),
                result.get("link", ""),
            )

    # --- Post-loop resolution ---

    # If we found a debunking result but nothing confirming → False.
    if best_contradicting_result is not None and best_same_topic_result is None:
        snippet = best_contradicting_result.get("snippet", "")
        return (
            "False",
            snippet or "Trusted sources indicate this claim is false or a common myth.",
            best_contradicting_result.get("link", ""),
        )

    # Numeric claim with same-topic result but mismatched numbers → Inaccurate.
    if best_same_topic_result is not None:
        return (
            "Inaccurate",
            best_same_topic_result.get(
                "snippet",
                "Related trusted evidence found, but numbers differ.",
            ),
            best_same_topic_result.get("link", ""),
        )

    # Nothing useful found.
    return (
        "False",
        "No relevant trusted evidence found for this claim.",
        trusted_results[0].get("link", ""),
    )


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def verify_claims(claims: List[str]) -> List[Dict[str, str]]:
    """Verify all claims one-by-one and return rows for the UI table."""
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