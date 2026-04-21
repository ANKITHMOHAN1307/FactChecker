# Fact-Check Web App (Streamlit + Python)

A simple web app that uploads a PDF, extracts factual claims, and returns a direct verdict for each claim:

- **Verified**
- **Not Verified**

## Features

- Upload a PDF in Streamlit.
- Extract claim-like lines from text.
- Verify each claim using the **Groq API**.
- Show a clean table with claim + verdict.

## Tech Stack

- Python
- Streamlit
- pdfplumber
- requests
- Groq API

## Files

```text
/workspace/FactChecker
├── app.py
├── extractor.py
├── verifier.py
├── requirements.txt
└── README.md
```

## Local Run

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Add your Groq key:

```bash
export GROQ_API_KEY="your_groq_api_key"
```

3. Start app:

```bash
streamlit run app.py
```

## Streamlit Cloud Deployment

1. Push this repo to GitHub.
2. Create a new app at https://share.streamlit.io/.
3. Set **Main file path** to `app.py`.
4. Add this secret:

```toml
GROQ_API_KEY = "your_groq_api_key"
```

5. Deploy and open your public URL.

## Output Format

The app output is intentionally minimal:

| Extracted Claim | Status |
|---|---|
| "Global EV sales were 14 million in 2023" | Verified |
| "XYZ company revenue was $900B" | Not Verified |

## Notes

- The verifier is intentionally simple and gives only direct verdict output.
- No domain/source ranking logic is used.
