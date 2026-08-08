# Log Anomaly Explainer

Paste or upload a log file, and it automatically detects error/warning/exception blocks and generates an AI-powered root-cause analysis for each — built for quick SRE-style triage.

## Features

- **Paste or upload** raw log text (`.log` / `.txt`)
- **Auto-detects anomaly blocks**: groups `ERROR`, `CRITICAL`, `FATAL`, `Exception`, `Traceback`, and `WARNING` lines together with their continuation lines (e.g. stack traces)
- **Local severity tagging** (Critical / Error / Warning / Info) with no API call needed
- **AI-generated triage report** per anomaly:
  1. Root Cause
  2. Likely Severity/Impact
  3. Immediate Mitigation Steps
  4. Long-Term Fix
  5. What To Check Next
- **Download** the analysis as a `.txt` file

## Tech Stack

- Python
- Streamlit
- OpenRouter API (free-tier model)
- Regex-based log parsing

## Setup

1. Clone the repo and install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Get a free API key from [OpenRouter](https://openrouter.ai/)

3. Add it to `.streamlit/secrets.toml`:
   ```toml
   OPENROUTER_API_KEY = "your-key-here"
   ```

4. Run the app:
   ```bash
   streamlit run app.py
   ```

## Deployment (Streamlit Community Cloud)

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io/) and deploy from the repo
3. In app settings → **Secrets**, add:
   ```toml
   OPENROUTER_API_KEY = "your-key-here"
   ```

## Usage

1. Paste log text or upload a `.log`/`.txt` file
2. Click **Scan for Anomalies**
3. Select a detected anomaly from the dropdown
4. Click **Explain This Anomaly** for an AI-generated triage report
5. Download the report if needed

## requirements.txt

```
streamlit
requests
```

## Notes

- Uses OpenRouter's free-tier model, which can rate-limit under heavy use — consider adding retry/backoff for demos.
- Detection is regex-based (no ML), so it works offline for the parsing step and only calls the API when you request an explanation.
