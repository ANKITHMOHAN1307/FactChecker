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
    "Upload a PDF, detect factual claims, and verify them. "
    "The app labels each claim as Verified or Not Verified."
)

# Read API key from Streamlit secrets if available
if "GROQ_API_KEY" in st.secrets:
    os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]

if not os.getenv("GROQ_API_KEY"):
    st.info("Add GROQ_API_KEY in environment/secrets to enable verification.")

uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])
start_clicked = st.button("Start Verification", type="primary")


def build_results_table(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Convert internal keys into user-friendly table columns."""
    return [
        {
            "Extracted Claim": row.get("claim", ""),
            "Status": row.get("status", ""),
        }
        for row in rows
    ]


if start_clicked:
    if not uploaded_file:
        st.warning("Please upload a PDF before starting verification.")
    else:
        with st.spinner("Extracting claims and verifying..."):
            # Extract lines and detect claim-like statements
            pdf_bytes = io.BytesIO(uploaded_file.read())
            lines = extract_text_lines_from_pdf(pdf_bytes)
            claims = detect_factual_claims(lines)

            if not claims:
                st.info("No strong factual claims were detected in this PDF.")
            else:
                # Verify each claim
                results = verify_claims(claims)
                table_rows = build_results_table(results)
                st.success(f"Done. Processed {len(claims)} claims.")
                st.dataframe(table_rows, use_container_width=True, hide_index=True)

                # Quick status summary
                verified_count = sum(1 for row in results if row["status"] == "Verified")
                not_verified_count = sum(1 for row in results if row["status"] == "Not Verified")

                st.caption(f"Verified: {verified_count} | Not Verified: {not_verified_count}")
