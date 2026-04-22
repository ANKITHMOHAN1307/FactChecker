
# FactChecker

[![Live App](https://img.shields.io/badge/Live%20Demo-Streamlit-green?style=for-the-badge&logo=streamlit)](https://factchecker-intern-assessment.streamlit.app/)

A lightweight Streamlit app that extracts factual claims from uploaded PDFs and verifies them using live web evidence.

## Overview
FactChecker helps you quickly check whether statements in a document are supported by trusted online sources.

## Project Workflow
1. Upload a PDF in the Streamlit interface.
2. `extractor.py` reads PDF text page by page.
3. Claim-like sentences are split and deduplicated.
4. `verifier.py` searches each claim via SerpAPI.
5. Evidence is selected (trusted domains are preferred).
6. If `GROQ_API_KEY` is available, Groq classifies claims as:
   - **Verified**
   - **Inaccurate**
7. If evidence is missing or unusable, status is **No Evidence Found**.
8. `app.py` displays results in a table with:
   - Extracted Claim
   - Status
   - Source Link

## Project Structure
```text
FactChecker/
├── app.py            # Streamlit UI and app flow
├── extractor.py      # PDF text extraction and claim preparation
├── verifier.py       # Web search, evidence selection, and verdict logic
├── requirements.txt  # Dependencies
└── README.md
```

## Requirements
- Python 3.10+
- SerpAPI key (required for web verification)
- Groq API key (optional, improves classification)

## Setup
```bash
pip install -r requirements.txt
export SERPAPI_API_KEY="your_serpapi_key"
export GROQ_API_KEY="your_groq_api_key"   # optional
```

## Run the App
```bash
streamlit run app.py
```

## Output Meaning
- **Verified**: evidence supports the claim.
- **Inaccurate**: evidence found, but claim appears incorrect or mismatched.
- **No Evidence Found**: no reliable supporting evidence retrieved.

## Notes
- Verification quality depends on source quality and search results.
- This is an assessment level woking project.
