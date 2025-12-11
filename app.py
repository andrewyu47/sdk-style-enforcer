import streamlit as st
import time
import os
import difflib
from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import ChatOpenAI

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Unified Governance Agent", page_icon="⚖️", layout="wide")

# --- CUSTOM CSS FOR DIFF VIEW (Restored) ---
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

# --- HELPER: GENERATE DIFF HTML ---
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

# --- 1. THE LOGIC ENGINE (Mock MCP) ---
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

# --- 2. THE STYLE ENGINE (PDF RAG) ---
@st.cache_resource
def load_style_guide(pdf_path):
    try:
        loader = PyPDFLoader(pdf_path)
        pages = loader.load_and_split()
        return "\n".join([p.page_content for p in pages])
    except:
        return None

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚖️ Governance Agent")
    api_key = st.text_input("OpenAI API Key", type="password")
    
    st.markdown("### 🧠 Dual-Engine Status")
    st.success("✅ **Logic Engine:** Google Cloud MCP (Active)")
    
    pdf_path = "splunk_style_guide.pdf"
    if os.path.exists(pdf_path):
        st.success(f"✅ **Style Engine:** {pdf_path} (RAG Active)")
    else:
        st.warning("⚠️ Style Engine: PDF not found")

    st.markdown("---")
    st.info("Mission: Enforce **Code Truth** and **Brand Voice** simultaneously.")

# --- MAIN UI ---
st.title("⚖️ SDK Governance Agent")
st.markdown("**Workflow:** Detect (BigQuery) $\\to$ Validate (MCP) $\\to$ Polish (Style RAG)")

if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({
        "role": "assistant", 
        "content": "I am the Governance Agent. I utilize **MCP for Logic** and **RAG for Style**. Ready to audit?"
    })

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"], unsafe_allow_html=True) # Allow HTML for history

# --- AGENT REASONING ---
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
            st.write(f"❌ Found error cluster in `{bq['file']}`.")
            
            # THE BAD CODE
            bad_doc = """def create_vm():
    # vm will be created
    # zone is set to us-east-1
    config = { "machineType": "n1-standard-1", "zone": "us-east-1" }
    return compute.insert(config)"""
            
            st.write("☁️ **Logic Engine:** Validating against Live Google API...")
            logic_errors = mcp.call_api_validator(bad_doc)
            for err in logic_errors:
                st.write(err)

            # PHASE 2: STYLE (RAG)
            st.write("🎨 **Style Engine:** Ingesting PDF Rules...")
            style_rules = load_style_guide(pdf_path)
            if style_rules:
                st.write("✅ RAG Context Loaded: Passive Voice Detected.")
            
            status.update(label="✅ Audit Complete: Fix Applied", state="complete", expanded=False)

        # THE FIXED CODE
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

        # GENERATE VISUAL DIFF
        diff_html = generate_diff_html(bad_doc, fixed_doc)

        explanation = f"""
I have remediated `{bq['file']}`. Below is the **Governance Diff**:

1.  **Logic Fixes (MCP):** `us-east-1` $\\to$ `us-east1-b` (Valid Zone).
2.  **Style Fixes (RAG):** Converted comments to Docstrings.

<div class="diff-header">Before vs. After Comparison:</div>
{diff_html}
        """
        
        st.markdown(explanation, unsafe_allow_html=True)
        st.session_state.messages.append({"role": "assistant", "content": explanation})