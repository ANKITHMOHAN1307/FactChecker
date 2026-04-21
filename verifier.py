"""Claim verification logic using Groq API."""

from __future__ import annotations

import json
import os
from typing import Dict, List

import requests

GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.1-8b-instant"


def _call_groq_for_verdict(claim: str, api_key: str) -> str:
    """Ask Groq for a binary verdict: Verified or Not Verified."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    # Keep prompt strict so output is easy to parse
    prompt = (
        "You are a fact-checking assistant. "
        "Given one claim, respond with JSON only in this exact format: "
        '{"status":"Verified"} or {"status":"Not Verified"}. '
        "Use only one of those two values."
    )

    payload = {
        "model": GROQ_MODEL,
        "temperature": 0,
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": claim},
        ],
        "response_format": {"type": "json_object"},
    }

    try:
        response = requests.post(GROQ_ENDPOINT, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        status = parsed.get("status", "Not Verified")

        if status not in {"Verified", "Not Verified"}:
            return "Not Verified"
        return status
    except (requests.RequestException, KeyError, IndexError, json.JSONDecodeError):
        return "Not Verified"


def verify_claims(claims: List[str]) -> List[Dict[str, str]]:
    """Verify all claims and return simple status-only output."""
    api_key = os.getenv("GROQ_API_KEY", "")
    rows: List[Dict[str, str]] = []

    for claim in claims:
        if not api_key:
            status = "Not Verified"
        else:
            status = _call_groq_for_verdict(claim, api_key)

        rows.append({"claim": claim, "status": status})

    return rows
