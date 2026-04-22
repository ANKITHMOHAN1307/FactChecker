"""
Simple fact verification using SerpAPI + Groq
Flow: claim → SerpAPI search → extract evidence → Groq decides Accurate/Inaccurate
"""

from __future__ import annotations

import json
import os
from typing import Dict, List, Optional, Tuple

import requests


SERPAPI_URL = "https://serpapi.com/search.json"
GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.1-8b-instant"

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
    return any(domain in link for domain in TRUSTED_DOMAINS)


def search_claim(claim: str, api_key: str) -> List[Dict]:
    """Search full claim using SerpAPI and return organic results."""
    if not api_key:
        return []

    params = {
        "engine": "google",
        "q": claim,
        "api_key": api_key,
        "num": 5,
    }

    try:
        response = requests.get(SERPAPI_URL, params=params, timeout=20)
        response.raise_for_status()
        data = response.json()
        return data.get("organic_results", [])
    except Exception:
        return []


def _fetch_evidence_and_source(
    claim: str, serpapi_key: str
) -> Tuple[str, str]:
    """
    Search SerpAPI for the claim, then extract the best evidence text
    and source URL from trusted results. Falls back to first result if
    no trusted source is found.
    Returns (evidence_text, source_url).
    """
    results = search_claim(claim, serpapi_key)

    if not results:
        return "", ""

    # Prefer trusted sources
    trusted = [r for r in results if is_trusted(r.get("link", ""))]
    best = trusted[0] if trusted else results[0]

    evidence = f"{best.get('title', '')} {best.get('snippet', '')}".strip()
    source_url = best.get("link", "")

    return evidence, source_url


def _ask_groq_accuracy(
    claim: str, evidence: str, source_url: str, groq_api_key: str
) -> str:
    """Use Groq to classify claim accuracy from provided evidence and source."""
    headers = {
        "Authorization": f"Bearer {groq_api_key}",
        "Content-Type": "application/json",
    }
    prompt = (
        "You are a strict fact-checking assistant. "
        "Given a claim, evidence text, and source URL, decide if the claim is accurate. "
        "Respond as JSON only: {\"status\":\"Accurate\"} or {\"status\":\"Inaccurate\"}. "
        "If evidence is weak, missing, unrelated, or uncertain, choose Inaccurate."
    )
    user_content = (
        f"Claim: {claim}\n"
        f"Evidence: {evidence or 'No evidence text available.'}\n"
        f"Source URL: {source_url or 'No source URL available.'}"
    )
    payload = {
        "model": GROQ_MODEL,
        "temperature": 0,
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_content},
        ],
        "response_format": {"type": "json_object"},
    }

    try:
        response = requests.post(
            GROQ_ENDPOINT, headers=headers, json=payload, timeout=30
        )
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        status = parsed.get("status", "Inaccurate")
        return status if status in {"Accurate", "Inaccurate"} else "Inaccurate"
    except (requests.RequestException, KeyError, IndexError, json.JSONDecodeError):
        return "Inaccurate"


def verify_claims(claims: List[str]) -> List[Dict]:
    """
    For each claim:
      1. Search SerpAPI to find evidence + source URL
      2. Pass evidence to Groq to decide Accurate / Inaccurate
      3. Return rows for Streamlit table
    """
    serpapi_key = os.getenv("SERPAPI_API_KEY", "")   # used for search
    groq_key = os.getenv("GROQ_API_KEY", "")          # used for AI decision

    rows = []

    for claim in claims:
        # Step 1 — fetch evidence via SerpAPI
        evidence, source_url = _fetch_evidence_and_source(claim, serpapi_key)

        # Step 2 — ask Groq to make the final call
        if not groq_key:
            status = "Inaccurate"
        else:
            status = _ask_groq_accuracy(claim, evidence, source_url, groq_key)

        # Step 3 — collect result
        rows.append(
            {
                "claim": claim,
                "status": status,
                "correct_information": evidence,
                "source_link": source_url,
            }
        )

    return rows