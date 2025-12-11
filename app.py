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