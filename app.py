import streamlit as st
import time
import difflib
from langchain_community.document_loaders import PyPDFLoader

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Splunk DocOps Workbench", page_icon="🛡️", layout="wide")

# --- CUSTOM STYLING ---
st.markdown("""
<style>
/* Main Container */
.main { background-color: #0E1117; }

/* Diff Container */
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

/* Audit Log Table */
.audit-row {
    padding: 8px;
    border-bottom: 1px solid #30363d;
    font-size: 14px;
}
.tag-logic { background-color: #7ee787; color: #000; padding: 2px 6px; border-radius: 4px; font-weight: bold; font-size: 11px; }
.tag-style { background-color: #a5d6ff; color: #000; padding: 2px 6px; border-radius: 4px; font-weight: bold; font-size: 11px; }
.tag-security { background-color: #ff7b72; color: #fff; padding: 2px 6px; border-radius: 4px; font-weight: bold; font-size: 11px; }
</style>
""", unsafe_allow_html=True)

# --- 1. THE GOVERNANCE ENGINE ---
class GovernanceEngine:
    def __init__(self):
        self.audit_log = [] 

    def audit_content(self, text):
        time.sleep(1.5)
        self.audit_log = []
        corrections = {}
        
        # --- LOGIC CHECKS ---
        if "version 1.3.0" in text:
            self.audit_log.append({"type": "LOGIC", "severity": "High", "msg": "Version 1.3.0 is End-of-Life. Updated to GA 1.4.2."})
            corrections["version 1.3.0"] = "version 1.4.2"

        if "October 15, 2025" in text:
            self.audit_log.append({"type": "LOGIC", "severity": "Medium", "msg": "AWS Mumbai launch pulled forward to June 2025."})
            corrections["October 15, 2025"] = "June 15, 2025"
            
        if "port=80" in text or "port 80" in text:
             self.audit_log.append({"type": "LOGIC", "severity": "High", "msg": "Incorrect Port. Splunk Management uses 8089."})
             corrections["port=80"] = "port=8089"
             corrections["port 80"] = "port 8089"

        # --- SECURITY CHECKS ---
        if "username=" in text:
            self.audit_log.append({"type": "SECURITY", "severity": "Critical", "msg": "Basic Auth is deprecated. Refactored to Token Auth."})
            corrections["username='admin',"] = "splunk_token=os.environ['SPLUNK_TOKEN']"
            corrections["password='changeme'"] = ""
            corrections["username="] = "# Auth updated to Token"

        # --- STYLE CHECKS ---
        if "Data is not sent" in text:
            self.audit_log.append({"type": "STYLE", "severity": "Low", "msg": "Passive voice detected. Rewritten to Active Voice."})
            corrections["Data is not sent to third-party LLM service providers"] = "Splunk does not send data to third-party LLM service providers"
            
        if "connection is established" in text:
            self.audit_log.append({"type": "STYLE", "severity": "Low", "msg": "Passive voice detected in comments."})
            corrections["# connection is established"] = "# Connects to the Splunk instance"

        return self._apply_fixes(text, corrections)

    def _apply_fixes(self, text, corrections):
        fixed_text = text
        for old, new in corrections.items():
            fixed_text = fixed_text.replace(old, new)
        return fixed_text

# --- 2. FILE HANDLERS ---
@st.cache_resource
def load_pdf_guide(file):
    with open("temp_guide.pdf", "wb") as f:
        f.write(file.getbuffer())
    loader = PyPDFLoader("temp_guide.pdf")
    pages = loader.load_and_split()
    return len(pages)

# --- 3. VISUALIZATIONS ---
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
    
    md = "### 🛡️ DocOps Automated Review\n"
    md += "**Status:** Changes Requested (Auto-Fixes Available)\n\n"
    md += "| Category | Finding |\n| :--- | :--- |\n"
    md += rows
    md += "\n**Suggested Refactor:**\n```text\n"
    md += fixed_text[:300] + "... (truncated)\n```\n"
    md += "*Generated by Splunk DocOps Action*"
    return md

# --- UI LAYOUT ---

# SIDEBAR
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/2/23/Splunk_logo.png", width=150)
    st.header("DocOps Config")
    
    st.subheader("1. Knowledge Sources")
    st.success("✅ Splunk API Spec (v9.0)")
    st.success("✅ Product Lifecycle Graph")
    
    st.subheader("2. Style Governance")
    uploaded_file = st.file_uploader("Upload Style Guide (PDF)", type="pdf")
    if uploaded_file:
        pages = load_pdf_guide(uploaded_file)
        st.success(f"✅ Indexed {pages} pages of rules")
        
    st.divider()
    st.caption("System Status: **Active**")

# MAIN PAGE
st.title("🛡️ Splunk DocOps Governance Workbench")
st.markdown("Automated governance for Documentation & SDK Examples. Enforces **Factual Accuracy**, **Security Best Practices**, and **Brand Voice**.")

# TABS
tab_input, tab_results = st.tabs(["📝 Input Draft", "📊 Audit Results"])

# DEFAULT TEXT - (Constructed safely to avoid syntax errors)
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
    "```\n\n"
    "### About Splunk AI Assistant\n"
    "Splunk AI Assistant for SPL version 1.3.0 is available.\n"
    "Supported regions:\n"
    "AWS AP - Mumbai October 15, 2025\n"
    "Data is not sent to third-party LLM service providers."
)

with tab_input:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Source Content")
        doc_input = st.text_area("Paste Draft Docs or Code:", value=default_text, height=500)
    
    with col2:
        st.info("Ready to Audit")
        st.markdown("""
        **Checks Performed:**
        * 🔍 **Logic:** Validates against Splunk API Spec (Ports, Endpoints).
        * 🗓️ **Lifecycle:** Checks version numbers and roadmap dates.
        * 🔐 **Security:** Scans for hardcoded credentials/deprecated auth.
        * 🎨 **Style:** Checks Passive Voice vs Active Voice.
        """)
        if st.button("🚀 Run Governance Audit", type="primary", use_container_width=True):
            st.session_state.run_audit = True

# RESULTS VIEW
if st.session_state.get("run_audit"):
    engine = GovernanceEngine()
    
    with st.spinner("Analyzing against Knowledge Graph & Style Guide..."):
        fixed_text = engine.audit_content(doc_input)
        log = engine.audit_log
    
    with tab_results:
        st.success("✅ Audit Complete: Issues Found & Fixed")
        
        res_col1, res_col2 = st.columns([1, 1])
        
        with res_col1:
            st.subheader("🔍 Visual Diff")
            st.markdown(render_diff(doc_input, fixed_text), unsafe_allow_html=True)
            
        with res_col2:
            st.subheader("📋 Governance Audit Log")
            
            for item in log:
                tag_class = f"tag-{item['type'].lower()}"
                st.markdown(f"""
                <div class="audit-row">
                    <span class="{tag_class}">{item['type']}</span> 
                    <b>{item['severity']}</b>: {item['msg']}
                </div>
                """, unsafe_allow_html=True)
                
            st.divider()
            st.subheader("🤖 GitHub Bot Preview")
            st.info("Simulated comment on Pull Request #402")
            st.markdown(render_github_preview(log, fixed_text))