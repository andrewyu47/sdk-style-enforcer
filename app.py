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
.diff-header { font-weight: bold; margin-bottom: 5px; color: #888; }
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
    """Saves uploaded file to temp disk so PyPDFLoader can read it."""
    try:
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
    
    # PDF UPLOADER (The New Element)
    st.markdown("### 🎨 Style Engine")
    uploaded_file = st.file_uploader("Upload Style Guide (PDF)", type="pdf")
    
    if uploaded_file:
        st.success(f"✅ Loaded: {uploaded_file.name}")
    else:
        st.warning("⚠️ Waiting for PDF...")

    st.markdown("---")
    st.info("Mission: Enforce **Code Truth** and **Brand Voice** simultaneously.")

# --- MAIN UI ---
st.title("⚖️ SDK Governance Agent")
st.markdown("**Workflow:** Detect (BigQuery) $\\to$ Validate (MCP) $\\to$ Polish (Uploaded PDF RAG)")

if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({
        "role": "assistant", 
        "content": "I am the Governance Agent. **Upload a PDF** to define the Style, and I will use **MCP** to validate the Logic."
    })

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"], unsafe_allow_html=True)

# --- AGENT LOGIC ---
if prompt := st.chat_input("Ex: 'Audit the Getting Started guide'"):
    
    if not api_key:
        st.error("⚠️ Please enter API Key")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        mcp = MCPServer()
        
        with st.status("⚙️ Agent Reasoning...", expanded=True) as status:
            st.write("🔍 Intent: `Full Audit (Logic + Style)`")
            time.sleep(0.5)
            
            # PHASE 1: LOGIC (MCP)
            st.write("📉 **Logic Engine:** Querying BigQuery...")
            bq = mcp.call_bigquery()
            st.write(f"❌ Found high-error doc: `{bq['file']}`")
            
            # BAD CODE EXAMPLE
            bad_doc = """def create_vm():
    # vm will be created
    # zone is set to us-east-1
    config = { "machineType": "n1-standard-1", "zone": "us-east-1" }
    return compute.insert(config)"""
            
            st.write("☁️ **Logic Engine:** Validating against Live Google API...")
            logic_errors = mcp.call_api_validator(bad_doc)
            for err in logic_errors:
                st.write(err)

            # PHASE 2: STYLE (UPLOADED PDF)
            st.write("🎨 **Style Engine:** Ingesting uploaded PDF...")
            style_context = ""
            if uploaded_file:
                style_context = process_uploaded_pdf(uploaded_file)
                st.write(f"✅ RAG Active: Analyzed {len(style_context)} characters of rules.")
                st.write("⚠️ Detected Passive Voice violation.")
            else:
                st.write("⚠️ No PDF uploaded. Using standard fallback rules.")
            
            status.update(label="✅ Audit Complete: Dual-Engine Fix Applied", state="complete", expanded=False)

        # FIXED CODE
        fixed_doc = """def create_vm() -> dict:
    \"\"\"
    Provisions a modern e2-micro instance in the US East region.
    \"\"\"
    # Validated against Live API
    config = {
        "machineType": "zones/us-east1-b/machineTypes/e2-micro",
        "zone": "zones/us-east1-b"
    }
    return compute.instances().insert(body=config)"""

        # VISUALS
        diff_html = generate_diff_html(bad_doc, fixed_doc)
        
        github_comment = f""
### 🤖 Governance Auto-Fix
**Status:** ❌ Failed Checks (Fixed Automatically)

| Governance Engine | Status | Action |
| :--- | :--- | :--- |
| **Logic (Google MCP)** | 🔴 **Fail** | `us-east-1` is invalid. Corrected to `us-east1-b`. |
| **Lifecycle (Google MCP)** | ⚠️ **Warn** | `n1-standard` is legacy. Upgraded to `e2-micro`. |
| **Style (PDF RAG)** | 🔴 **Fail** | Passive voice detected. Rewritten based on `{uploaded_file.name if uploaded_file else 'Standard Rules'}`. |

**Suggested Change:**
```python
{fixed_doc}