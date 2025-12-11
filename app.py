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

# DEFAULT TEXT - (Broken into parts to be safe)
part1 = """### Connecting to Splunk
You can use this function to connect to port 80.

```python
def connect():
    # connection is established
    return client.connect(
        host='localhost',
        port=80, 
        username='admin', 
        password='changeme'
    )