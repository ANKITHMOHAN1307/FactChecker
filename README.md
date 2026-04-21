 (cd "$(git rev-parse --show-toplevel)" && git apply --3way <<'EOF' 
diff --git a/.gitignore b/.gitignore
new file mode 100644
index 0000000000000000000000000000000000000000..bc563d21433b31fabae127f8f0391d2d6886c6e2
--- /dev/null
+++ b/.gitignore
@@ -0,0 +1,12 @@
+# Python
+__pycache__/
+*.py[cod]
+*.egg-info/
+.venv/
+venv/
+
+# Streamlit secrets
+.streamlit/secrets.toml
+
+# OS
+.DS_Store
diff --git a/README.md b/README.md
index 45c1e5e0067a5286dc5c403af4fa269a21290a95..30110151635a99c6fdaaf5b1161ced4f2dd9abd7 100644
--- a/README.md
+++ b/README.md
@@ -1,2 +1,98 @@
-# FactChecker
-"Fact-Checking  App" that automates claim verification.  Marketing content  stats which pass through the  tool acting as a "Truth Layer" Reads a PDF, cross-referencing claims against live web data, and flagging inaccuracies
+# Fact-Check Web App (Streamlit + Python)
+
+A simple web app that lets you upload a PDF and automatically fact-check claim-like lines (percentages, money values, years, and technical numbers) using live web search.
+
+## What this project does
+
+- Uploads a PDF file.
+- Extracts text line by line.
+- Detects factual claims using regex patterns.
+- Sends each full claim sentence to live web search (SerpAPI).
+- Labels each claim as:
+  - **Verified** (trusted source matches)
+  - **Inaccurate** (similar claim exists, but numbers look different/outdated)
+  - **False** (no strong trusted evidence)
+
+## How it works (simple flow)
+
+1. **PDF Extraction** (`extractor.py`)
+   - Uses `pdfplumber` to read text from all pages.
+2. **Claim Detection** (`extractor.py`)
+   - Keeps lines with factual signals such as `%`, currency, years, million/billion, and technical units.
+   - Filters out very short and heading-like lines.
+3. **Verification** (`verifier.py`)
+   - Uses **full claim sentence** as query in SerpAPI.
+   - Checks trusted domains and compares numbers in evidence snippets.
+4. **UI Output** (`app.py`)
+   - Displays results in a table with claim, status, correction/evidence, and source link.
+
+## Tech stack
+
+- Python
+- Streamlit
+- pdfplumber
+- requests
+- SerpAPI (Google Search results API)
+
+## Project structure
+
+```text
+fact_check_app/
+│
+├── app.py
+├── extractor.py
+├── verifier.py
+├── requirements.txt
+├── README.md
+└── .gitignore
+```
+
+> In this repository, these files are in the root for easy Streamlit deployment.
+
+## Run locally
+
+1. Create and activate a virtual environment (optional but recommended).
+2. Install dependencies:
+
+```bash
+pip install -r requirements.txt
+```
+
+3. Set your SerpAPI key:
+
+```bash
+export SERPAPI_API_KEY="your_key_here"
+```
+
+4. Run the app:
+
+```bash
+streamlit run app.py
+```
+
+## Deploy on Streamlit Community Cloud
+
+1. Push this repository to GitHub.
+2. In Streamlit Community Cloud, create a new app from this repo.
+3. Set **Main file path** to `app.py`.
+4. Add secret:
+   - `SERPAPI_API_KEY = "your_key_here"`
+5. Deploy.
+
+The deployed app works exactly like local run: upload PDF → click **Start Verification** → view fact-check table.
+
+## Example workflow
+
+1. Upload a report PDF.
+2. App detects lines like:
+   - "Revenue increased by 32% in Q2 2024"
+   - "The company reached $5 billion valuation"
+3. App searches web using the full line.
+4. App shows result status + best trusted source link.
+
+## Notes for assignment/interview
+
+- Code is intentionally simple and function-based.
+- Logic is retrieval-first and explainable.
+- No heavy AI pipeline or overengineering.
+- Easy to extend with better domain rules later.
diff --git a/app.py b/app.py
new file mode 100644
index 0000000000000000000000000000000000000000..79eafd8e9965bb65020af701daf8e2f2ceed86d3
--- /dev/null
+++ b/app.py
@@ -0,0 +1,65 @@
+"""Streamlit UI for the fact-check web app."""
+
+from __future__ import annotations
+
+import io
+from typing import List, Dict
+
+import streamlit as st
+
+from extractor import extract_text_lines_from_pdf, detect_factual_claims
+from verifier import verify_claims
+
+
+st.set_page_config(page_title="Fact-Check Web App", page_icon="✅", layout="wide")
+
+st.title("📄 Fact-Check Web App")
+st.write(
+    "Upload a PDF, detect factual claims, and verify them using live web search. "
+    "The app labels each claim as Verified, Inaccurate, or False."
+)
+
+uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])
+start_clicked = st.button("Start Verification", type="primary")
+
+# Read key from Streamlit secrets if available (useful in cloud deployment).
+if "SERPAPI_API_KEY" in st.secrets:
+    import os
+
+    os.environ["SERPAPI_API_KEY"] = st.secrets["SERPAPI_API_KEY"]
+
+
+def build_results_table(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
+    """Convert internal keys into user-friendly table columns."""
+    return [
+        {
+            "Extracted Claim": row.get("claim", ""),
+            "Status": row.get("status", ""),
+            "Correct Information": row.get("correct_information", ""),
+            "Source Link": row.get("source_link", ""),
+        }
+        for row in rows
+    ]
+
+
+if start_clicked:
+    if not uploaded_file:
+        st.warning("Please upload a PDF before starting verification.")
+    else:
+        with st.spinner("Extracting claims and verifying with live search..."):
+            pdf_bytes = io.BytesIO(uploaded_file.read())
+            lines = extract_text_lines_from_pdf(pdf_bytes)
+            claims = detect_factual_claims(lines)
+
+            if not claims:
+                st.info("No strong factual claims were detected in this PDF.")
+            else:
+                results = verify_claims(claims)
+                table_rows = build_results_table(results)
+                st.success(f"Done. Processed {len(claims)} claims.")
+                st.dataframe(table_rows, use_container_width=True, hide_index=True)
+
+                st.caption(
+                    "Tip: Add SERPAPI_API_KEY in Streamlit secrets or environment variables "
+                    "to improve live verification quality."
+                )
diff --git a/extractor.py b/extractor.py
new file mode 100644
index 0000000000000000000000000000000000000000..3e46c4855103bb6b573aa06bd59eb0b0ff821931
--- /dev/null
+++ b/extractor.py
@@ -0,0 +1,76 @@
+"""PDF extraction and claim-detection helpers."""
+
+from __future__ import annotations
+
+import io
+import re
+from typing import Iterable, List
+
+import pdfplumber
+
+# Regex patterns that identify claim-like numeric statements.
+CLAIM_PATTERNS = [
+    re.compile(r"\b\d{1,3}(?:,\d{3})*(?:\.\d+)?%\b"),  # percentages like 32%
+    re.compile(r"[$₹€£]\s?\d+(?:,\d{3})*(?:\.\d+)?\b"),  # currencies
+    re.compile(r"\b(19|20)\d{2}\b"),  # years like 2024
+    re.compile(r"\b\d+(?:\.\d+)?\s?(million|billion|trillion)\b", re.I),
+    re.compile(r"\bQ[1-4]\b", re.I),  # quarter numbers (Q1/Q2)
+    re.compile(r"\b\d+(?:\.\d+)?\s?(km|kg|gb|tb|mhz|ghz|mw|kw)\b", re.I),
+    re.compile(r"\b\d{1,2}\s?(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s?\d{2,4}\b", re.I),
+]
+
+# Very short, title-like lines are usually noise for this task.
+MIN_LINE_LENGTH = 25
+
+
+
+def extract_text_lines_from_pdf(pdf_file: io.BytesIO) -> List[str]:
+    """Extract text from every PDF page and return clean non-empty lines."""
+    all_lines: List[str] = []
+
+    with pdfplumber.open(pdf_file) as pdf:
+        for page in pdf.pages:
+            text = page.extract_text() or ""
+            page_lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
+            all_lines.extend(page_lines)
+
+    return all_lines
+
+
+
+def is_meaningful_line(line: str) -> bool:
+    """Filter out obvious headings and incomplete fragments."""
+    if len(line) < MIN_LINE_LENGTH:
+        return False
+
+    # Skip heading-like all-caps lines without punctuation.
+    if line.isupper() and not re.search(r"[.,:;%$₹€£]", line):
+        return False
+
+    # Skip lines that have too few words.
+    if len(line.split()) < 5:
+        return False
+
+    return True
+
+
+
+def detect_factual_claims(lines: Iterable[str]) -> List[str]:
+    """Return unique lines that look like factual/statistical claims."""
+    claims: List[str] = []
+    seen = set()
+
+    for raw_line in lines:
+        line = " ".join(raw_line.split())
+        if not is_meaningful_line(line):
+            continue
+
+        has_claim_signal = any(pattern.search(line) for pattern in CLAIM_PATTERNS)
+        if not has_claim_signal:
+            continue
+
+        if line not in seen:
+            seen.add(line)
+            claims.append(line)
+
+    return claims
diff --git a/requirements.txt b/requirements.txt
new file mode 100644
index 0000000000000000000000000000000000000000..fa89fdb78450e6ef796e7c0479c8a453268e5027
--- /dev/null
+++ b/requirements.txt
@@ -0,0 +1,3 @@
+streamlit>=1.40.0
+pdfplumber>=0.11.4
+requests>=2.32.0
diff --git a/verifier.py b/verifier.py
new file mode 100644
index 0000000000000000000000000000000000000000..3635809d98aac10ad2b3c52dabc555c6d9c99a6c
--- /dev/null
+++ b/verifier.py
@@ -0,0 +1,174 @@
+"""Claim verification logic using SerpAPI web search results."""
+
+from __future__ import annotations
+
+import os
+import re
+from typing import Dict, List, Optional, Set, Tuple
+
+import requests
+
+SERPAPI_ENDPOINT = "https://serpapi.com/search.json"
+TRUSTED_DOMAINS = [
+    ".gov",
+    ".edu",
+    "worldbank.org",
+    "imf.org",
+    "oecd.org",
+    "un.org",
+    "who.int",
+    "reuters.com",
+    "bloomberg.com",
+    "statista.com",
+]
+
+STOPWORDS = {
+    "the",
+    "a",
+    "an",
+    "and",
+    "or",
+    "of",
+    "in",
+    "to",
+    "for",
+    "on",
+    "with",
+    "by",
+    "from",
+    "at",
+    "is",
+    "was",
+    "were",
+    "be",
+    "as",
+    "that",
+    "this",
+    "it",
+}
+
+
+
+def _extract_numbers(text: str) -> List[str]:
+    """Step 1/2: Extract numbers using the requested regex pattern."""
+    # Requested pattern from review instructions.
+    return re.findall(r"\d+\.?\d*", text)
+
+
+
+def _normalize_keywords(text: str) -> Set[str]:
+    """Small helper to compare if claim and snippet are about the same topic."""
+    words = re.findall(r"[a-zA-Z]{3,}", text.lower())
+    return {w for w in words if w not in STOPWORDS}
+
+
+
+def _is_trusted(url: str) -> bool:
+    return any(domain in url for domain in TRUSTED_DOMAINS)
+
+
+
+def search_claim(claim: str, api_key: Optional[str]) -> List[Dict[str, str]]:
+    """Run a live Google search through SerpAPI using the full claim sentence."""
+    if not api_key:
+        return []
+
+    params = {
+        "engine": "google",
+        "q": claim,  # full claim, not isolated numbers
+        "api_key": api_key,
+        "num": 5,
+    }
+
+    try:
+        response = requests.get(SERPAPI_ENDPOINT, params=params, timeout=20)
+        response.raise_for_status()
+        data = response.json()
+        return data.get("organic_results", [])
+    except requests.RequestException:
+        return []
+
+
+
+def classify_claim(claim: str, results: List[Dict[str, str]]) -> Tuple[str, str, str]:
+    """Classify claim with explicit numeric-comparison layer before final status."""
+    if not results:
+        return (
+            "False",
+            "No search evidence found (check API key or internet access).",
+            "",
+        )
+
+    trusted_results = [r for r in results if _is_trusted(r.get("link", ""))]
+    if not trusted_results:
+        return (
+            "False",
+            "No trusted-source result found for this claim.",
+            results[0].get("link", ""),
+        )
+
+    # Step 1: Extract numbers from claim.
+    claim_numbers = set(_extract_numbers(claim))
+    claim_keywords = _normalize_keywords(claim)
+
+    best_related_result: Optional[Dict[str, str]] = None
+
+    for result in trusted_results:
+        evidence_text = f"{result.get('title', '')} {result.get('snippet', '')}"
+
+        # Step 2: Extract numbers from trusted source snippet.
+        evidence_numbers = set(_extract_numbers(evidence_text))
+        evidence_keywords = _normalize_keywords(evidence_text)
+
+        overlap_count = len(claim_keywords.intersection(evidence_keywords))
+        same_topic = overlap_count >= 2
+
+        # Step 3: Compare numbers first for final class.
+        if claim_numbers and evidence_numbers and claim_numbers == evidence_numbers:
+            return (
+                "Verified",
+                result.get("snippet", "Trusted source supports this claim."),
+                result.get("link", ""),
+            )
+
+        if same_topic:
+            best_related_result = result
+
+    # Different numbers but same topic -> Inaccurate.
+    if best_related_result is not None:
+        return (
+            "Inaccurate",
+            best_related_result.get(
+                "snippet",
+                "Related trusted evidence found, but numbers appear different or updated.",
+            ),
+            best_related_result.get("link", ""),
+        )
+
+    # No relevant evidence -> False.
+    return (
+        "False",
+        "No relevant trusted evidence found for this claim.",
+        trusted_results[0].get("link", ""),
+    )
+
+
+
+def verify_claims(claims: List[str]) -> List[Dict[str, str]]:
+    """Verify all claims one-by-one and prepare output rows for the UI table."""
+    api_key = os.getenv("SERPAPI_API_KEY", "")
+    rows: List[Dict[str, str]] = []
+
+    for claim in claims:
+        results = search_claim(claim, api_key=api_key)
+        status, correct_information, source_link = classify_claim(claim, results)
+        rows.append(
+            {
+                "claim": claim,
+                "status": status,
+                "correct_information": correct_information,
+                "source_link": source_link,
+            }
+        )
+
+    return rows
 
EOF
)