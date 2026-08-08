import streamlit as st
import requests
import re

st.set_page_config(page_title="Log Anomaly Explainer")

OPEN_ROUTER_API_KEY = st.secrets.get("OPENROUTER_API_KEY", "")
MODEL = "openrouter/free"

ANOMALY_PATTERN = re.compile(
    r"(ERROR|CRITICAL|FATAL|Exception|Traceback|WARN(?:ING)?)",
    re.IGNORECASE
)

if "anomalies" not in st.session_state:
    st.session_state.anomalies = []
if "selected_index" not in st.session_state:
    st.session_state.selected_index = 0


def parse_log(text):
    """Group log lines into anomaly blocks. A block starts at a line
    matching ANOMALY_PATTERN and absorbs indented / continuation
    lines that follow (e.g. stack traces)."""
    lines = text.splitlines()
    blocks = []
    current = []

    def flush():
        if current:
            blocks.append("\n".join(current).strip())

    for line in lines:
        if ANOMALY_PATTERN.search(line):
            flush()
            current = [line]
        elif current:
            # continuation line (traceback frame, indented detail, etc.)
            if line.strip() == "" and len(current) > 1:
                flush()
                current = []
            else:
                current.append(line)
    flush()

    # de-dupe near-identical blocks, cap to keep the UI usable
    seen = set()
    unique_blocks = []
    for b in blocks:
        key = b.splitlines()[0] if b else b
        if key not in seen:
            seen.add(key)
            unique_blocks.append(b)
    return unique_blocks[:50]


def guess_severity(block):
    upper = block.upper()
    if "CRITICAL" in upper or "FATAL" in upper:
        return "Critical"
    if "ERROR" in upper or "EXCEPTION" in upper or "TRACEBACK" in upper:
        return "Error"
    if "WARN" in upper:
        return "Warning"
    return "Info"


def explain_anomaly(block):
    prompt = f"""
You are an experienced Site Reliability Engineer triaging a production log.

Log excerpt:
{block}

Provide:
1. Root Cause
2. Likely Severity/Impact
3. Immediate Mitigation Steps
4. Long-Term Fix
5. What To Check Next (monitoring/queries to run)
"""
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPEN_ROUTER_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": MODEL,
            "messages": [{"role": "user", "content": prompt}]
        },
        timeout=30
    )
    if response.status_code != 200:
        err = response.json().get("error", {})
        msg = err.get("message", response.text)
        return f"Error {response.status_code}: {msg}"
    return response.json()["choices"][0]["message"]["content"]


st.title("Log Anomaly Explainer")
st.write("Paste or upload a log file. It detects error/warning blocks and generates an AI root-cause analysis for each.")

input_mode = st.radio("Input method", ["Paste text", "Upload file"], horizontal=True)

log_text = ""
if input_mode == "Paste text":
    log_text = st.text_area("Log contents", height=250, placeholder="Paste raw log output here...")
else:
    uploaded = st.file_uploader("Upload a .log or .txt file", type=["log", "txt"])
    if uploaded is not None:
        log_text = uploaded.read().decode("utf-8", errors="ignore")

if st.button("Scan for Anomalies"):
    if not log_text.strip():
        st.error("No log content provided.")
        st.stop()
    with st.spinner("Scanning log..."):
        st.session_state.anomalies = parse_log(log_text)
        st.session_state.selected_index = 0
    if not st.session_state.anomalies:
        st.info("No ERROR/WARNING/Exception patterns found in this log.")

if st.session_state.anomalies:
    st.success(f"Found {len(st.session_state.anomalies)} anomaly block(s).")

    selected_block = st.selectbox(
        "Choose an Anomaly",
        st.session_state.anomalies,
        index=st.session_state.selected_index,
        format_func=lambda b: f"[{guess_severity(b)}] {b.splitlines()[0][:80]}"
    )

    with st.expander("Raw Anomaly Block"):
        st.code(selected_block, language="log")

    if st.button("Explain This Anomaly"):
        with st.spinner("Analyzing with AI..."):
            explanation = explain_anomaly(selected_block)
        st.subheader("AI Analysis")
        st.markdown(explanation)
        st.download_button(
            "Download Analysis",
            data=explanation,
            file_name="anomaly_analysis.txt",
            mime="text/plain"
        )
