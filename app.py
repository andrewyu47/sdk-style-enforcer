import streamlit as st
import time
import os
import difflib
from langchain_community.document_loaders import PyPDFLoader

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

# --- 1. THE LOGIC ENGINE (Mock MCP Router) ---
class MCPRouter:
    def __init__(self, mode):
        self.mode = mode

    def detect_issues(self):
        time.sleep(1)
        
        if self.mode == "Google Cloud":
            return {
                "file": "docs/provision_vm.md",
                "error": "400 Bad Request: Invalid Zone",
                "bad_code": """def create_vm():
    # vm will be created
    # zone is set to us-east-1
    config = { "machineType": "n1-standard-1", "zone": "us-east-1" }
    return compute.insert(config)"""
            }
            
        elif self.mode == "NVIDIA Omniverse":
            return {
                "file": "exts/create_prop.py",
                "error": "RuntimeError: Stage Not Found",
                "bad_code": """def create_cube():
    # cube will be created
    # stage is opened manually
    stage = Usd.Stage.Open("test.usd")
    return stage.DefinePrim("/Cube", "Cube")"""
            }
            
        else: # Standard Python (The Restored Mode)
            return {
                "file": "utils/data_processor.py",
                "error": "PEP8 Violation: Missing Type Hints & Docstrings",
                "bad_code": """def process(x, y):
    # data is processed here
    # result is returned
    z = x * y
    return z"""
            }

    def validate_and_fix(self, bad_code):
        time.sleep(1)
        report = []
        fixed_code = ""

        if self.mode == "Google Cloud":
            report.append("❌ **Logic Error (MCP):** `us-east-1` is an AWS zone. Google Cloud requires `us-east1-b`.")
            report.append("⚠️ **Deprecation (MCP):** `n1-standard-1` is legacy. Use `e2-micro`.")
            fixed_code = """def create_vm() -> dict:
    \"\"\"
    Provisions a modern e2-micro instance in the US East region.
    \"\"\"
    # Validated against Live API
    config = {
        "machineType": "zones/us-east1-b/machineTypes/e2-micro",
        "zone": "zones/us-east1-b"
    }
    return compute.instances().insert(body=config)"""

        elif self.mode == "NVIDIA Omniverse":
            report.append("❌ **Context Error (MCP):** Do not open stages manually. Use `omni.usd.get_context()`.")
            fixed_code = """import omni.usd
from pxr import Usd, UsdGeom

async def create_cube() -> Usd.Prim:
    \"\"\"
    Asynchronously creates a cube primitive in the active stage.
    \"\"\"
    # Validated against Omniverse Kit
    ctx = omni.usd.get_context()
    stage = ctx.get_stage()
    return stage.DefinePrim("/Cube", "Cube")"""
            
        else: # Standard Python Fixes
            report.append("❌ **PEP8 Error:** Missing Type Hints for arguments and return value.")
            report.append("⚠️ **Naming Convention:** Variables `x, y, z` are non-semantic.")
            fixed_code = """def process_data(input_val: int, multiplier: int) -> int:
    \"\"\"
    Multiplies the input value by the multiplier.
    
    Args:
        input_val (int): The primary data input.
        multiplier (int): The factor to multiply by.
    \"\"\"
    # Refactored for Type Safety
    result = input_val * multiplier
    return result"""
            
        return report, fixed_code

# --- 2. STYLE ENGINE (Upload Handler) ---
@st.cache_resource
def process_uploaded_pdf(uploaded_file):
    try:
        with open("temp_style_guide.pdf", "wb") as f:
            f.write(uploaded_file.getbuffer())
        loader = PyPDFLoader("temp_style_guide.pdf")
        pages = loader.load_and_split()
        return "\n".join([p.page_content for p in pages])
    except:
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
    
# --- HELPER TO RESET CHAT ON MODE CHANGE ---
    def reset_conversation():
        st.session_state.messages = []

    # 3 MODES NOW AVAILABLE (With Reset Trigger)
    st.markdown("### 🔌 Logic Engine (MCP)")
    ecosystem_mode = st.selectbox(
        "Select Ecosystem", 
        ["Google Cloud", "NVIDIA Omniverse", "Standard Python (PEP8)"],
        on_change=reset_conversation  # <--- THIS IS THE FIX
    )
    
    # Dynamic Status Indicators
    if ecosystem_mode == "Google Cloud":
        st.success("✅ `mcp-server-bigquery` (Active)")
        st.success("✅ `mcp-server-compute` (Active)")
    elif ecosystem_mode == "NVIDIA Omniverse":
        st.success("✅ `mcp-server-omniverse` (Active)")
    else:
        st.success("✅ `flake8-linter` (Active)")
        st.success("✅ `mypy-type-checker` (Active)")

    st.markdown("### 🎨 Style Engine (RAG)")
    uploaded_file = st.file_uploader("Upload Style Guide (PDF)", type="pdf")
    
    if uploaded_file:
        st.success(f"✅ Loaded: {uploaded_file.name}")
    else:
        st.warning("⚠️ Waiting for PDF...")

    st.markdown("---")
    st.info("Mission: Enforce **Code Truth** and **Brand Voice**.")

# --- MAIN UI ---
st.title(f"⚖️ {ecosystem_mode} Governance Agent")
st.markdown("**Workflow:** Detect (Analytics) $\\to$ Validate (MCP) $\\to$ Polish (Uploaded PDF RAG)")

if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({
        "role": "assistant", 
        "content": f"I am connected to the **{ecosystem_mode} Mesh**. Ready to audit?"
    })

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"], unsafe_allow_html=True)

# --- AGENT LOGIC ---
if prompt := st.chat_input("Ex: 'Audit the codebase'"):
    
    if not api_key:
        st.error("⚠️ Please enter API Key")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        mcp = MCPRouter(ecosystem_mode)
        
        with st.status("⚙️ Agent Reasoning...", expanded=True) as status:
            st.write(f"🔍 Intent: `Full Audit ({ecosystem_mode})`")
            time.sleep(0.5)
            
            # PHASE 1: DETECTION
            st.write("📉 **Logic Engine:** Scanning Codebase...")
            data = mcp.detect_issues()
            st.write(f"❌ Found issue in `{data['file']}`: {data['error']}")
            
            bad_code = data['bad_code']
            
            # PHASE 2: VALIDATION
            st.write(f"☁️ **Logic Engine:** Validating Logic Rules...")
            logic_errors, fixed_code = mcp.validate_and_fix(bad_code)
            for err in logic_errors:
                st.write(err)

            # PHASE 3: STYLE
            st.write("🎨 **Style Engine:** Checking Brand Voice...")
            if uploaded_file:
                process_uploaded_pdf(uploaded_file)
                st.write(f"✅ RAG Active: Analyzed PDF rules.")
                st.write("⚠️ Detected Passive Voice violation.")
            else:
                st.write("⚠️ No PDF uploaded. Using standard fallback.")
            
            status.update(label="✅ Audit Complete: Fix Applied", state="complete", expanded=False)

        # VISUALS
        diff_html = generate_diff_html(bad_code, fixed_code)
        
        pdf_name = uploaded_file.name if uploaded_file else 'Standard Rules'
        
        # Dynamic Table Logic
        logic_row = ""
        if ecosystem_mode == "Google Cloud":
            logic_row = "| **Logic (Google MCP)** | 🔴 **Fail** | `us-east-1` invalid. Fixed to `us-east1-b`. |"
        elif ecosystem_mode == "NVIDIA Omniverse":
            logic_row = "| **Logic (NVIDIA MCP)** | 🔴 **Fail** | Manual Stage Open invalid. Fixed to `get_context()`. |"
        else:
            logic_row = "| **Logic (PEP8/MyPy)** | 🔴 **Fail** | Missing Types. Added hints & semantic names. |"

        header = "### 🤖 Governance Auto-Fix\n**Status:** ❌ Failed Checks (Fixed Automatically)\n"
        table = f"""
| Governance Engine | Status | Action |
| :--- | :--- | :--- |
{logic_row}
| **Style (PDF RAG)** | 🔴 **Fail** | Passive voice rewritten based on `{pdf_name}`. |
"""
        code_block = f"\n**Suggested Change:**\n```python\n{fixed_code}\n```"
        github_comment = header + table + code_block

        st.write("---")
        tab1, tab2 = st.tabs(["👀 Manager View (Visual Diff)", "🤖 CI/CD Bot View (GitHub)"])
        
        with tab1:
            st.markdown(diff_html, unsafe_allow_html=True)
            
        with tab2:
            st.info("Simulated Pull Request Comment:")
            st.markdown(github_comment)

        st.session_state.messages.append({"role": "assistant", "content": "Audit Complete."})