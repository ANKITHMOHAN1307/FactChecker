"""Streamlit UI for the fact-check web app."""

from __future__ import annotations

import io
from typing import List, Dict

import streamlit as st

from extractor import extract_text_lines_from_pdf, detect_factual_claims
from verifier import verify_claims


st.set_page_config(page_title="Fact-Check Web App", page_icon="✅", layout="wide")

st.title("📄 Fact-Check Web App")
st.write(
    "Upload a PDF, detect factual claims, and verify them using live web search. "
    "The app labels each claim as Verified, Inaccurate, or False."
)

uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])
start_clicked = st.button("Start Verification", type="primary")

# Read key from Streamlit secrets if available (useful in cloud deployment).
if "SERPAPI_API_KEY" in st.secrets:
    import os

    os.environ["SERPAPI_API_KEY"] = st.secrets["SERPAPI_API_KEY"]


def build_results_table(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Convert internal keys into user-friendly table columns."""
    return [
        {
            "Extracted Claim": row.get("claim", ""),
            "Status": row.get("status", ""),
            "Correct Information": row.get("correct_information", ""),
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
                st.success(f"Done. Processed {len(claims)} claims.")
                st.dataframe(table_rows, use_container_width=True, hide_index=True)

                st.caption(
                    "Tip: Add SERPAPI_API_KEY in Streamlit secrets or environment variables "
                    "to improve live verification quality."
                )
