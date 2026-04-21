# Fact-Check Web App (Streamlit + Python)

A simple web app that uploads a PDF, extracts factual claims, checks those claims against live web data, and marks each claim as **Verified**, **Inaccurate**, or **False**.

---

## Features

- **Extract** factual claim-like lines from a PDF (stats, years, money, technical values).
- **Verify** claims with live Google results via SerpAPI.
- **Report** with clear statuses:
  - **Verified**: trusted evidence supports the claim.
  - **Inaccurate**: trusted evidence exists but conflicts/looks outdated.
  - **False**: no credible evidence found.

---

## Tech Stack

- Python
- Streamlit
- pdfplumber
- requests
- SerpAPI

---

## Project Structure

```text
/workspace/FactChecker
├── app.py
├── extractor.py
├── verifier.py
├── requirements.txt
└── README.md
```

---

## Local Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Add your SerpAPI key:

```bash
export SERPAPI_API_KEY="your_serpapi_key"
```

3. Run app:

```bash
streamlit run app.py
```

4. Open the local URL shown by Streamlit and upload your PDF.

---

## Deployment (Mandatory Requirement)

Use **Streamlit Community Cloud**:

1. Push this repository to GitHub.
2. Go to https://share.streamlit.io/ and create a new app.
3. Set **Main file path** to `app.py`.
4. In app settings → **Secrets**, add:

```toml
SERPAPI_API_KEY = "your_serpapi_key"
```

5. Deploy and copy your public URL.

### After Deploy

- Test by uploading your own PDF.
- Click **Start Verification**.
- Review claim-by-claim status and source links.

> Note: Deployment URL depends on your Streamlit account/repo name and is created during your own deploy step.

---

## How Verification Works

1. `extractor.py` reads PDF text line by line.
2. It keeps lines likely to contain factual claims.
3. `verifier.py` sends each claim to live search.
4. The verifier checks trusted sources and number overlap.
5. UI displays final status and source link.

---

## Example Output

| Extracted Claim | Status | Correct Information | Source Link |
|---|---|---|---|
| "Revenue grew 25% in 2024" | Inaccurate | Trusted sources found, but values do not match this claim. | https://... |
| "X country population is 1.4 billion" | Verified | Claim is supported by overlapping values in trusted source. | https://... |
| "Y is the capital of Z" | False | No credible trusted source found for this claim. | https://... |

---

## Notes

- Code is intentionally simple and readable.
- Comments are kept basic for easy review.
- You can improve accuracy by expanding trusted sources and adding stronger NLP claim extraction.
