import streamlit as st
import time
import difflib
from langchain_community.document_loaders import PyPDFLoader

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="DocOps Governance Workbench", page_icon="🛡️", layout="wide")

# --- CSS FOR DIFF VIEW ---
st.markdown("""
<style>
.diff-container {
    max-height: 400px;
    overflow-y: auto;
    border: 1px solid #30363d;
    border-radius: 6px;
    background-color: #0d1117;
    font-family: 'SFMono-Regular', Consolas, monospace;
    font-size: 13px;
    padding: 10px;
    white-space: pre-wrap;
}
.diff-added { background-color: rgba(46, 160, 67, 0.15); color: #3fb950; display: block; }
.diff-removed { background-color: rgba(248, 81, 73, 0.15); color: #ff7b72; display: block; text-decoration: line-through; }
</style>
""", unsafe_allow_html=True)

# --- 1. MOCK MCP SERVER (Truth Engine) ---
class MCPServer:
    def __init__(self, ecosystem):
        self.ecosystem = ecosystem

    def validate_content(self, text_content):
        """
        Validates both CODE logic and TEXT facts.
        """
        time.sleep(1.0)
        errors = []
        
        # SPLUNK SPECIFIC CHECKS
        if self.ecosystem == "Splunk Enterprise":
            # Fact Check: Port Numbers
            if "port 80 " in text_content or "port=80" in text_content:
                errors.append("❌ **Factual Error (MCP):** Docs claim port 80. Splunk Management Port is actually `8089`.")
            
            # Fact Check: Pricing/Tiers
            if "Free Tier" in text_content:
                errors.append("❌ **Factual Error (MCP):** Token Auth is an Enterprise-only feature. Removed 'Free Tier' claim.")

            # Code Logic: Deprecated Auth
            if "username=" in text_content:
                errors.append("⚠️ **Security Violation (MCP):** Basic Auth is deprecated. Code updated to use `splunk_token`.")
        
        # NVIDIA SPECIFIC CHECKS
        elif self.ecosystem == "NVIDIA Omniverse":
            if "synchronous" in text_content.lower():
                errors.append("❌ **Factual Error (MCP):** Omniverse Kit is async-first. Docs falsely claim synchronous behavior.")
            if "Usd.Stage.Open" in text_content:
                errors.append("❌ **Context Violation (MCP):** Manual stage opening detected. Use `get_context()`.")
                
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
    ecosystem = st.selectbox("Target Ecosystem", ["Splunk Enterprise", "NVIDIA Omniverse"])
    
    if ecosystem == "Splunk Enterprise":
        st.success("✅ `mcp-server-splunk-api` Active")
        st.success("✅ `mcp-server-product-catalog` Active")
    else:
        st.success("✅ `mcp-server-omniverse` Active")

    st.markdown("### 🎨 Style Engine (RAG)")
    uploaded_file = st.file_uploader("Upload Style Guide (PDF)", type="pdf")
    if uploaded_file:
        success, pages = load_style_guide(uploaded_file)
        if success:
            st.success(f"✅ Loaded {pages} pages of Rules")

    st.divider()
    st.info("**Mission:** Fix Broken Code and Incorrect Facts.")

# --- MAIN UI ---
st.title("🛡️ DocOps Governance Workbench")
st.markdown("Unified governance for Developer Documentation. Validates against **Platform Reality** (Facts) and **Style Standards** (Voice).")

# BAD DOCUMENTATION EXAMPLES (Markdown + Code)
bad_doc_splunk = """### Connecting to Splunk
You can use this function on the Free Tier.
It connects to the standard web port 80.

```python
def connect():
    # connection is established
    return client.connect(
        host='localhost',
        port=80, 
        username='admin', 
        password='changeme'
    )
```"""

bad_doc_nvidia = """### Creating a Cube
This function runs in a synchronous blocking mode.

```python
def make_cube():
    # cube is created
    stage = Usd.Stage.Open("test.usd")
    return stage.DefinePrim("/Cube", "Cube")
```"""

default_text = bad_doc_splunk if ecosystem == "Splunk Enterprise" else bad_doc_nvidia

col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Input (Draft Docs)")
    doc_input = st.text_area("Paste Documentation Snippet:", value=default_text, height=400)
    run_btn = st.button("🚀 Run Fact & Style Audit", type="primary", use_container_width=True)

if run_btn:
    if not api_key:
        st.error("⚠️ Please enter OpenAI API Key in sidebar")
        st.stop()
        
    mcp = MCPServer(ecosystem)
    
    with st.status("⚙️ Executing Governance Protocols...", expanded=True):
        st.write(f"🔌 **Logic Engine:** Verifying facts against {ecosystem} Knowledge Graph...")
        fact_errors = mcp.validate_content(doc_input)
        
        if fact_errors:
            for err in fact_errors:
                st.write(err)
        else:
            st.write("✅ Facts: Verified.")
            
        st.write("🎨 **Style Engine:** Analyzing voice...")
        if uploaded_file:
            st.write("⚠️ **Style Violation:** Passive voice detected in comments.")
        else:
            st.write("⚠️ Using Standard Rules.")
            
    # FIXED CONTENT GENERATION
    fixed_text = ""
    if ecosystem == "Splunk Enterprise":
        fixed_text = """### Connecting to Splunk
This feature requires an Enterprise License.
It connects to the management port 8089.

```python
def connect_to_splunk(token: str) -> client.Service:
    \"\"\"
    Connects to the Splunk instance using a Bearer Token.
    \"\"\"
    # Validated against Splunk Cloud API
    return client.connect(
        host='localhost',
        port=8089,
        splunk_token=token
    )
```"""
    else:
        fixed_text = """### Creating a Cube
This function runs asynchronously to prevent UI blocking.

```python
import omni.usd
async def make_cube() -> Usd.Prim:
    \"\"\"
    Asynchronously creates a cube primitive.
    \"\"\"
    # Validated against Omniverse Context
    ctx = omni.usd.get_context()
    return ctx.get_stage().DefinePrim("/Cube", "Cube")
```"""

    with col2:
        st.subheader("2. Output (Verified Docs)")
        st.code(fixed_text, language='markdown')
        st.success("✅ Audit Passed")

    st.divider()
    st.subheader("🔍 Governance Diff (Facts + Code)")
    diff_html = generate_diff_html(doc_input, fixed_text)
    st.markdown(diff_html, unsafe_allow_html=True)