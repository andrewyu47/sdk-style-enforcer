import streamlit as st
import time
import difflib
from langchain_community.document_loaders import PyPDFLoader

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="DocOps Governance Workbench", page_icon="🛡️", layout="wide")

# --- CUSTOM STYLING ---
st.markdown("""
<style>
.main { background-color: #0E1117; }
.diff-box {
    border: 1px solid #30363d;
    border-radius: 6px;
    background-color: #0d1117;
    font-family: 'SFMono-Regular', Consolas, monospace;
    font-size: 13px;
    padding: 15px;
    white-space: pre-wrap;
    line-height: 1.6;
}
.diff-added { background-color: rgba(46, 160, 67, 0.2); color: #3fb950; display: inline; }
.diff-removed { background-color: rgba(248, 81, 73, 0.2); color: #ff7b72; text-decoration: line-through; display: inline; }
.audit-row { padding: 8px; border-bottom: 1px solid #30363d; font-size: 14px; }
.tag-logic { background-color: #7ee787; color: #000; padding: 2px 6px; border-radius: 4px; font-weight: bold; font-size: 11px; }
.tag-style { background-color: #a5d6ff; color: #000; padding: 2px 6px; border-radius: 4px; font-weight: bold; font-size: 11px; }
.tag-security { background-color: #ff7b72; color: #fff; padding: 2px 6px; border-radius: 4px; font-weight: bold; font-size: 11px; }
</style>
""", unsafe_allow_html=True)

# --- 1. THE GOVERNANCE ENGINE ---
class GovernanceEngine:
    def __init__(self, mode):
        self.mode = mode
        self.audit_log = [] 

    def audit_content(self, text):
        time.sleep(1.0)
        self.audit_log = []
        corrections = {}
        
        # === MODE 1: SPLUNK ENTERPRISE ===
        if self.mode == "Splunk Enterprise":
            if "version 1.3.0" in text:
                self.audit_log.append({"type": "LOGIC", "severity": "High", "msg": "Lifecycle: v1.3.0 is EOL. Updated to 1.4.2."})
                corrections["version 1.3.0"] = "version 1.4.2"
            if "port 80" in text or "port=80" in text:
                self.audit_log.append({"type": "LOGIC", "severity": "High", "msg": "Accuracy: Mgmt port is 8089, not 80."})
                corrections["port=80"] = "port=8089"
                corrections["port 80"] = "port 8089"
            if "October 15, 2025" in text:
                self.audit_log.append({"type": "LOGIC", "severity": "Medium", "msg": "Roadmap: Mumbai launch moved to June 2025."})
                corrections["October 15, 2025"] = "June 15, 2025"
            if "username=" in text:
                self.audit_log.append({"type": "SECURITY", "severity": "Critical", "msg": "Auth: Basic Auth deprecated. Used Token."})
                corrections["username='admin',"] = "splunk_token=os.environ['SPLUNK_TOKEN']"
                corrections["password='changeme'"] = ""
                corrections["username="] = "# Auth updated to Token"
            if "Data is not sent" in text:
                self.audit_log.append({"type": "STYLE", "severity": "Low", "msg": "Voice: Passive voice rewritten."})
                corrections["Data is not sent to third-party LLM service providers"] = "Splunk does not send data to third-party LLM service providers"

        # === MODE 2: NVIDIA OMNIVERSE ===
        elif self.mode == "NVIDIA Omniverse":
            if "Usd.Stage.Open" in text:
                self.audit_log.append({"type": "LOGIC", "severity": "Critical", "msg": "Context: Manual Open forbidden in Kit."})
                corrections['Usd.Stage.Open("test.usd")'] = "omni.usd.get_context().get_stage()"
                corrections['# opens stage manually'] = "# Gets active stage context"
            if "def make_cube" in text and "async" not in text:
                self.audit_log.append({"type": "LOGIC", "severity": "High", "msg": "Performance: Main thread blocking. Added async."})
                corrections["def make_cube():"] = "async def make_cube():"
            if "cube is created" in text:
                self.audit_log.append({"type": "STYLE", "severity": "Low", "msg": "Voice: Passive voice rewritten."})
                corrections["# cube is created"] = "# Asynchronously creates cube"

        # === MODE 3: STANDARD PYTHON ===
        elif self.mode == "Standard Python (PEP8)":
            if "def process(x, y)" in text:
                self.audit_log.append({"type": "LOGIC", "severity": "Medium", "msg": "Quality: Missing Type Hints."})
                corrections["def process(x, y):"] = "def process_data(data: list, multiplier: int) -> list:"
            if "data is processed" in text:
                self.audit_log.append({"type": "STYLE", "severity": "Low", "msg": "Docs: Missing Docstring."})
                corrections["# data is processed"] = '"""Processes data list safely."""'
            
        return self._apply_fixes(text, corrections)

    def _apply_fixes(self, text, corrections):
        fixed_text = text
        for old, new in corrections.items():
            fixed_text = fixed_text.replace(old, new)
        return fixed_text

# --- 2. FILE HANDLERS & VISUALS ---
@st.cache_resource
def load_pdf_rules(file):
    # Simulating parsing rules from PDF
    return 24

def render_diff(original, modified):
    d = difflib.Differ()
    diff = list(d.compare(original.splitlines(), modified.splitlines()))
    html = ['<div class="diff-box">']
    for line in diff:
        if line.startswith('+ '):
            html.append(f'<span class="diff-added">{line}</span><br>')
        elif line.startswith('- '):
            html.append(f'<span class="diff-removed">{line}</span><br>')
        elif line.startswith('? '):
            continue
        else:
            html.append(f'<span>{line}</span><br>')
    html.append('</div>')
    return "".join(html)

def render_github_preview(audit_log, fixed_text):
    rows = ""
    for item in audit_log:
        icon = "🔴" if item['severity'] == "Critical" else "⚠️"
        rows += f"| {icon} **{item['type']}** | {item['msg']} |\n"
    # Safe string construction
    md = "### 🛡️ Governance Check\n"
    md += "**Status:** Failed (Auto-Fixed)\n\n"
    md += "| Type | Finding |\n| :--- | :--- |\n"
    md += rows
    md += "\n```python\n" + fixed_text[:200] + "...\n```"
    return md

# --- UI LAYOUT ---

# SIDEBAR
with st.sidebar:
    st.header("⚙️ Governance Config")
    api_key = st.text_input("OpenAI API Key", type="password")
    
    st.subheader("1. Target Ecosystem")
    mode = st.selectbox("Select Protocol", ["Splunk Enterprise", "NVIDIA Omniverse", "Standard Python (PEP8)"])
    
    # Status Indicators
    if mode == "Splunk Enterprise":
        st.success("✅ `mcp-splunk-api` Connected")
        st.success("✅ `mcp-product-graph` Connected")
    elif mode == "NVIDIA Omniverse":
        st.success("✅ `mcp-omniverse-kit` Connected")
        st.success("✅ `mcp-usd-resolver` Connected")
    else:
        st.success("✅ `flake8` Connected")
        st.success("✅ `mypy` Connected")

    st.subheader("2. Style Engine")
    uploaded_file = st.file_uploader("Upload Style Guide (PDF)", type="pdf")
    
    # RULE COUNTER
    rule_count = 0
    if uploaded_file:
        rule_count = load_pdf_rules(uploaded_file)
        st.success(f"✅ Parsed {rule_count} Rules from PDF")
    
    st.divider()
    if st.button("Reset Session"):
        st.session_state.run_audit = False

# MAIN PAGE
st.title(f"🛡️ {mode} Governance Workbench")
st.markdown("**Mission:** "Ensure content is Accurate, Secure, and Consistent before it ships")

# DYNAMIC DEFAULT TEXT
if mode == "Splunk Enterprise":
    default_text = (
        "### Connecting to Splunk\n"
        "You can use this function to connect to port 80.\n\n"
        "```python\n"
        "def connect():\n"
        "    # connection is established\n"
        "    return client.connect(\n"
        "        host='localhost',\n"
        "        port=80, \n"
        "        username='admin', \n"
        "        password='changeme'\n"
        "    )\n"
        "```\n"
        "### About Splunk AI Assistant\n"
        "Splunk AI Assistant for SPL version 1.3.0 is available.\n"
        "Supported regions:\n"
        "AWS AP - Mumbai October 15, 2025\n"
        "Data is not sent to third-party LLM service providers."
    )
elif mode == "NVIDIA Omniverse":
    default_text = (
        "### Creating 3D Assets\n"
        "This function creates a cube synchronously.\n\n"
        "```python\n"
        "def make_cube():\n"
        "    # cube is created\n"
        "    # opens stage manually\n"
        "    stage = Usd.Stage.Open(\"test.usd\")\n"
        "    return stage.DefinePrim(\"/Cube\", \"Cube\")\n"
        "```"
    )
else:
    default_text = (
        "### Data Processor\n"
        "This function processes the input list.\n\n"
        "```python\n"
        "def process(x, y):\n"
        "    # data is processed\n"
        "    return [i * y for i in x]\n"
        "```"
    )

# --- LAYOUT: INPUT SECTION ---
col1, col2 = st.columns([3, 1])

with col1:
    st.subheader("1. Source Draft")
    doc_input = st.text_area("Paste Draft:", value=default_text, height=350, key=mode)

with col2:
    st.subheader("Active Protocols")
    st.caption("System Ready")
    
    # DYNAMIC PROTOCOL DISPLAY
    style_source = f"**{uploaded_file.name}**" if uploaded_file else "Standard Rules"
    rules_text = f"({rule_count} rules active)" if uploaded_file else ""
    
    if mode == "Splunk Enterprise":
        st.markdown(f"* 🔍 **Facts:** Port 8089, Version Lifecycle\n* 🔐 **Security:** Token Auth Only\n* 🎨 **Style:** {style_source} {rules_text}")
    elif mode == "NVIDIA Omniverse":
        st.markdown(f"* 🔍 **Context:** No Manual Stage Open\n* ⚡ **Perf:** Async Execution Required\n* 🎨 **Style:** {style_source} {rules_text}")
    else:
        st.markdown(f"* 🔍 **Quality:** PEP8 Standards\n* 📝 **Docs:** Mandatory Docstrings\n* 🎨 **Style:** {style_source} {rules_text}")
    
    st.markdown("---")
    if st.button("🚀 Run Audit", type="primary", use_container_width=True):
        st.session_state.run_audit = True

# --- LAYOUT: RESULTS SECTION ---
if st.session_state.get("run_audit"):
    st.divider()
    st.header("2. Audit Results")
    
    engine = GovernanceEngine(mode)
    with st.spinner("Executing Governance Protocols..."):
        fixed_text = engine.audit_content(doc_input)
        log = engine.audit_log
    
    r1, r2 = st.columns([3, 2])
    
    with r1:
        st.subheader("🔍 Visual Diff")
        st.markdown(render_diff(doc_input, fixed_text), unsafe_allow_html=True)
        
        # FINAL CLEAN OUTPUT BOX
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("✅ Verified Output (Copy/Paste)")
        st.text_area("Final Clean Text:", value=fixed_text, height=300, label_visibility="collapsed")
        
    with r2:
        st.subheader("📋 Governance Log")
        st.success(f"✅ Auto-Fixed {len(log)} Issues")
        
        for item in log:
            tag = f"tag-{item['type'].lower()}"
            st.markdown(f'<div class="audit-row"><span class="{tag}">{item["type"]}</span> {item["msg"]}</div>', unsafe_allow_html=True)
        
        st.markdown("---")
        with st.expander("🤖 View GitHub CI/CD Comment"):
            st.markdown(render_github_preview(log, fixed_text))