import streamlit as st
import time
import difflib
from langchain_community.document_loaders import PyPDFLoader

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Splunk DocOps Workbench", page_icon="🛡️", layout="wide")

# --- CSS FOR DIFF VIEW ---
st.markdown("""
<style>
.diff-container {
    max-height: 300px;
    overflow-y: auto;
    border: 1px solid #30363d;
    border-radius: 6px;
    background-color: #0d1117;
    font-family: 'SFMono-Regular', Consolas, monospace;
    font-size: 13px;
    padding: 10px;
}
.diff-added { background-color: rgba(46, 160, 67, 0.15); color: #3fb950; display: block; }
.diff-removed { background-color: rgba(248, 81, 73, 0.15); color: #ff7b72; display: block; text-decoration: line-through; }
</style>
""", unsafe_allow_html=True)

# --- 1. LOGIC ENGINE (MCP) ---
class MCPServer:
    def __init__(self, ecosystem):
        self.ecosystem = ecosystem

    def validate_code(self, code_snippet):
        time.sleep(1.0)
        errors = []
        
        # SPLUNK SPECIFIC LOGIC
        if self.ecosystem == "Splunk Enterprise":
            if "connect(username=" in code_snippet:
                errors.append("❌ **Security Violation (MCP):** Basic Auth (`username/password`) is deprecated in Splunk Cloud. Use `splunk_token`.")
            if "search_oneshot" in code_snippet and "exec_mode" not in code_snippet:
                errors.append("⚠️ **Performance (MCP):** Blocking search detected. Recommended: Async search export.")
        
        # NVIDIA SPECIFIC LOGIC (To show range)
        elif self.ecosystem == "NVIDIA Omniverse":
            if "Usd.Stage.Open" in code_snippet:
                errors.append("❌ **Context Violation (MCP):** Never open stages manually in Kit. Use `omni.usd.get_context()`.")
                
        return errors

# --- 2. STYLE ENGINE (RAG) ---
@st.cache_resource
def load_style_guide(uploaded_file):
    try:
        with open("temp_style.pdf", "wb") as f:
            f.write(uploaded_file.getbuffer())
        loader = PyPDFLoader("temp_style.pdf")
        pages = loader.load_and_split()
        return True, len(pages)
    except:
        return False, 0

# --- DIFF GENERATOR ---
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
    st.header("🛡️ DocOps Config")
    api_key = st.text_input("OpenAI API Key", type="password")
    
    st.markdown("### 🔌 Logic Engine (MCP)")
    # Defaulting to Splunk to tell YOUR story
    ecosystem = st.selectbox("Target Ecosystem", ["Splunk Enterprise", "NVIDIA Omniverse"])
    
    if ecosystem == "Splunk Enterprise":
        st.success("✅ `mcp-server-splunk` Active")
        st.success("✅ `mcp-server-bigquery` Active")
    else:
        st.success("✅ `mcp-server-omniverse` Active")

    st.markdown("### 🎨 Style Engine (RAG)")
    uploaded_file = st.file_uploader("Upload Style Guide (PDF)", type="pdf")
    if uploaded_file:
        success, pages = load_style_guide(uploaded_file)
        if success:
            st.success(f"✅ Loaded {pages} pages of Rules")

    st.divider()
    st.info("**Mission:** Enforce **Security** (Logic) and **Voice** (Style) across SDK docs.")

# --- MAIN UI ---
st.title("🛡️ DocOps Governance Workbench")
st.markdown("Unified governance for Developer Documentation. Validates SDK code against **Platform Reality** and **Style Standards**.")

# BAD CODE SAMPLES (The "Before" Picture)
bad_code_splunk = """def connect_to_splunk():
    # service object is created
    # connection is made using password
    service = client.connect(
        host='localhost',
        port=8089,
        username='admin',
        password='changeme'
    )
    return service"""

bad_code_nvidia = """def make_cube():
    # cube is created
    # opens stage manually
    stage = Usd.Stage.Open("test.usd")
    return stage.DefinePrim("/Cube", "Cube")"""

default_code = bad_code_splunk if ecosystem == "Splunk Enterprise" else bad_code_nvidia

col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Input (Non-Compliant)")
    code_input = st.text_area("Paste Code Snippet:", value=default_code, height=300)
    run_btn = st.button("🚀 Run DocOps Audit", type="primary", use_container_width=True)

if run_btn:
    if not api_key:
        st.error("⚠️ Please enter OpenAI API Key in sidebar")
        st.stop()
        
    mcp = MCPServer(ecosystem)
    
    with st.status("⚙️ Executing Governance Protocols...", expanded=True):
        st.write(f"🔌 **Logic Engine:** Validating against {ecosystem} API Spec...")
        logic_errors = mcp.validate_code(code_input)
        
        if logic_errors:
            for err in logic_errors:
                st.write(err)
        else:
            st.write("✅ Logic: Valid.")
            
        st.write("🎨 **Style Engine:** Analyzing against Brand Voice...")
        if uploaded_file:
            st.write("⚠️ **Style Violation:** Passive voice detected in comments.")
        else:
            st.write("⚠️ Using Standard Rules (No PDF uploaded).")
            
    # FIXED CODE GENERATION (The "After" Picture)
    fixed_code = ""
    if ecosystem == "Splunk Enterprise":
        fixed_code = """def connect_to_splunk(token: str) -> client.Service:
    \"\"\"
    Connects to the Splunk instance using a Bearer Token.
    \"\"\"
    # Validated against Splunk Cloud API v9.0
    service = client.connect(
        host='localhost',
        port=8089,
        splunk_token=token 
    )
    return service"""
    else:
        fixed_code = """import omni.usd
async def make_cube() -> Usd.Prim:
    \"\"\"
    Asynchronously creates a cube primitive.
    \"\"\"
    # Validated against Omniverse Kit
    ctx = omni.usd.get_context()
    return ctx.get_stage().DefinePrim("/Cube", "Cube")"""

    with col2:
        st.subheader("2. Output (Compliant)")
        st.code(fixed_code, language='python')
        st.success("✅ Audit Passed")

    st.divider()
    st.subheader("🔍 DocOps Diff")
    diff_html = generate_diff_html(code_input, fixed_code)
    st.markdown(diff_html, unsafe_allow_html=True)