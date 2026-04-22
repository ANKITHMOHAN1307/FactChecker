"""Streamlit UI for the fact-check web app."""

from __future__ import annotations

import io
import os
from typing import Dict, List

import streamlit as st

from extractor import detect_factual_claims, extract_text_lines_from_pdf
from verifier import verify_claims

st.set_page_config(page_title="Fact-Check Web App", page_icon="✅", layout="wide")

st.title("📄 Fact-Check Web App")
st.write(
    "Upload a PDF, detect factual claims, and verify them using live web search. "
    "The app labels each claim as Accurate, Inaccurate, or No Evidence Found."
)

# Read API keys from Streamlit secrets if available
if "SERPAPI_API_KEY" in st.secrets:
    os.environ["SERPAPI_API_KEY"] = st.secrets["SERPAPI_API_KEY"]

if "GROQ_API_KEY" in st.secrets:
    os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]

if not os.getenv("SERPAPI_API_KEY"):
    st.info("Add SERPAPI_API_KEY in environment/secrets to enable live web verification.")

uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])
start_clicked = st.button("Start Verification", type="primary")


def build_results_table(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Convert internal keys into user-friendly table columns."""
    return [
        {
            "Extracted Claim": row.get("claim", ""),
            "Status": row.get("status", ""),
            "Source Link": row.get("source_link", ""),
        }
        for row in rows
    ]


if start_clicked:
    if not uploaded_file:
        st.warning("Please upload a PDF before starting verification.")
    else:
        with st.spinner("Extracting claims and verifying with live search..."):
            pdf_bytes = io.BytesIO(uploaded_file.read())
            lines = extract_text_lines_from_pdf(pdf_bytes)
            claims = detect_factual_claims(lines)

            if not claims:
                st.info("No strong factual claims were detected in this PDF.")
            else:
                results = verify_claims(claims)
                table_rows = build_results_table(results)

                # Count each status — "False" is now "No Evidence Found"
                accurate_count = sum(1 for r in results if r["status"] == "Verified")
                inaccurate_count = sum(1 for r in results if r["status"] == "Inaccurate")
                no_evidence_count = sum(1 for r in results if r["status"] == "No Evidence Found")

                st.success(f"Done. Processed {len(claims)} claims.")
                st.dataframe(table_rows, use_container_width=True, hide_index=True)

                # Summary row with all three counts
                st.caption(
                    f" Verified: {accurate_count} | "
                    f" Inaccurate: {inaccurate_count} | "
                    f" No Evidence Found: {no_evidence_count}"
                )