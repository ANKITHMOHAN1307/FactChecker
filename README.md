# Fact-Check Web App (Streamlit + Python)

A simple web app that lets you upload a PDF and automatically fact-check claim-like lines (percentages, money values, years, and technical numbers) using live web search.

## What this project does

- Uploads a PDF file.
- Extracts text line by line.
- Detects factual claims using regex patterns.
- Sends each full claim sentence to live web search (SerpAPI).
- Labels each claim as:
  - **Verified** (trusted source matches)
  - **Inaccurate** (similar claim exists, but numbers look different/outdated)
  - **False** (no strong trusted evidence)

## How it works (simple flow)

1. **PDF Extraction** (`extractor.py`)
   - Uses `pdfplumber` to read text from all pages.
2. **Claim Detection** (`extractor.py`)
   - Keeps lines with factual signals such as `%`, currency, years, million/billion, and technical units.
   - Filters out very short and heading-like lines.
3. **Verification** (`verifier.py`)
   - Uses **full claim sentence** as query in SerpAPI.
   - Checks trusted domains and compares numbers in evidence snippets.
4. **UI Output** (`app.py`)
   - Displays results in a table with claim, status, correction/evidence, and source link.

## Tech stack

- Python
- Streamlit
- pdfplumber
- requests
- SerpAPI (Google Search results API)

## Project structure

```text
fact_check_app/
│
├── app.py
├── extractor.py
├── verifier.py
├── requirements.txt
├── README.md
└── .gitignore
```

> In this repository, these files are in the root for easy Streamlit deployment.

## Run locally

1. Create and activate a virtual environment (optional but recommended).
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set your SerpAPI key:

```bash
export SERPAPI_API_KEY="your_key_here"
```

4. Run the app:

```bash
streamlit run app.py
```

## Deploy on Streamlit Community Cloud

1. Push this repository to GitHub.
2. In Streamlit Community Cloud, create a new app from this repo.
3. Set **Main file path** to `app.py`.
4. Add secret:
   - `SERPAPI_API_KEY = "your_key_here"`
5. Deploy.

The deployed app works exactly like local run: upload PDF → click **Start Verification** → view fact-check table.

## Example workflow

1. Upload a report PDF.
2. App detects lines like:
   - "Revenue increased by 32% in Q2 2024"
   - "The company reached $5 billion valuation"
3. App searches web using the full line.
4. App shows result status + best trusted source link.

## Notes for assignment/interview

- Code is intentionally simple and function-based.
- Logic is retrieval-first and explainable.
- No heavy AI pipeline or overengineering.
- Easy to extend with better domain rules later.
