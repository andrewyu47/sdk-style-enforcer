import streamlit as st
import time
import os
import difflib
from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import ChatOpenAI

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Unified Governance Agent", page_icon="⚖️", layout="wide")

# --- CSS FOR DIFF VIEW ---
st.markdown("""
<style>
.diff-container {
    max-height: 400px;
    overflow-y: auto;
    border: 1px solid #444;
    border-radius: 5px;
    background-color: #0E1117;
    font-family: monospace;
    font-size: 14px;
    padding: 10px;
    margin-top: 10px;
}
.diff-added { background-color: rgba(0, 255, 0, 0.2); display: block; }
.diff-removed { background-color: rgba(255, 0, 0, 0.2); display: block; text-decoration: line-through; }
</style>
""", unsafe_allow_html=True)

# --- 1. LOGIC ENGINE (Mock MCP) ---
class MCPServer:
    def call_bigquery(self):
        time.sleep(1) 
        return {
            "file": "docs/provision_vm.md",
            "error": "400 Bad Request: Invalid Zone",
            "tickets": "High Volume",
        }

    def call_api_validator(self, snippet):
        time.sleep(1)
        report = []
        if "us-east-1" in snippet:
            report.append("❌ **Logic Error (MCP):** `us-east-1` is an AWS zone. Google Cloud requires `us-east1-b`.")
        if "n1-standard-1" in snippet:
            report.append("⚠️ **Deprecation (MCP):** `n1-standard-1` is legacy. Use `e2-micro`.")
        return report

# --- 2. STYLE ENGINE (Upload Handler) ---
@st.cache_resource
def process_uploaded_pdf(uploaded_file):
    try:
        # Create temp file safely
        with open("temp_style_guide.pdf", "wb") as f:
            f.write(uploaded_file.getbuffer())
            
        loader = PyPDFLoader("temp_style_guide.pdf")
        pages = loader.load_and_split()
        return "\n".join([p.page_content for p in pages])
    except Exception as e:
        return None

# --- HELPER: DIFF GENERATOR ---
def generate_diff_html(original, refactored):
    d = difflib.Differ()
    diff = list(d.compare(original.splitlines(), refactored.splitlines()))
    html = ['<div class="diff-container">']
    for line in diff:
        if line.startswith('+ '):
            html.append(f'<span class="diff-added">{line}</span>')
        elif line.startswith('- '):
            html.append(f'<span class="diff-removed">{line}</span>')
        elif line.startswith('? '):
            continue
        else:
            html.append(f'<span>{line}</span>')
    html.append('</div>')
    return "\n".join(html)

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚖️ Governance Agent")
    api_key = st.text_input("OpenAI API Key", type="password")
    
    st.markdown("### 🧠 Dual-Engine Status")
    st.success("✅ **Logic Engine:** Google Cloud MCP (Active)")
    
    st.markdown("### 🎨 Style Engine")
    uploaded_file = st.file_uploader("Upload Style Guide (PDF)", type="pdf")
    
    if uploaded_file:
        st.success(f"✅ Loaded: {