# FactChecker

FactChecker is a simple Streamlit app that reads a PDF, extracts claim-like sentences, and checks them against live web search results.

## How it works
1. **Upload a PDF** in the web app.
2. `extractor.py` reads text from each page and splits it into sentence-like claims.
3. Duplicate claims are removed.
4. `verifier.py` searches each claim with **SerpAPI**.
5. It prefers trusted sources (for example `.gov`, `.edu`, Reuters, World Bank, etc.).
6. If `GROQ_API_KEY` is set, Groq classifies the claim as:
   - `Verified`
   - `Inaccurate`
7. If no usable source is found (or keys are missing), status becomes `No Evidence Found`.
8. `app.py` shows all results in a table with claim, status, and source link.

## Files
- `app.py` — Streamlit UI and workflow.
- `extractor.py` — PDF text extraction and claim detection.
- `verifier.py` — Search + evidence selection + claim classification.
- `requirements.txt` — Python dependencies.

## Run locally
```bash
pip install -r requirements.txt
export SERPAPI_API_KEY="your_key"
export GROQ_API_KEY="your_key"   # optional but recommended
streamlit run app.py
```
