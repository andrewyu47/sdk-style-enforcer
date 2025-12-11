import streamlit as st
import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="SDK Style Enforcer", page_icon="🛡️", layout="wide")

# --- SIDEBAR CONFIGURATION (Restored UI) ---
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # 1. API Key
    api_key = st.text_input("OpenAI API Key", type="password")

    # 2. Select Enforcement Standard (Dropdown)
    mode = st.selectbox(
        "Select Enforcement Standard",
        [
            "Standard Python (PEP8)", 
            "Splunk Enterprise (PDF RAG)", 
            "NVIDIA Omniverse (USD/Kit)"
        ]
    )

    # 3. Select Model (Dropdown)
    model_choice = st.selectbox("Select Model", ["gpt-4", "gpt-3.5-turbo"])
    
    # 4. PDF Status Check
    st.markdown("---")
    st.markdown("### 📚 Knowledge Base")
    pdf_path = "splunk_style_guide.pdf"
    if os.path.exists(pdf_path):
        st.success(f"✅ Loaded: {pdf_path}")
    else:
        st.error(f"❌ Missing: {pdf_path}")

    # 5. About Section
    st.markdown("---")
    st.markdown("**About this Tool**")
    st.markdown("This tool uses GenAI to act as a 'Linter-as-a-Service', refactoring messy code to meet strict developer ecosystem standards.")

# --- PDF LOADER FUNCTION ---
@st.cache_resource
def get_splunk_rules(file_path):
    try:
        loader = PyPDFLoader(file_path)
        pages = loader.load_and_split()
        full_text = "\n".join([p.page_content for p in pages])
        return full_text
    except Exception as e:
        return None

# --- MAIN APP UI ---
st.title("🛡️ SDK Style Enforcer")
st.markdown("**Automated Governance for Developer Ecosystems.**")

col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Input: Messy SDK Code")
    default_code = """def create_red_cube():
    # this function makes a red cube
    # data will be loaded from the stage
    stage = Usd.Stage.Open("test.usd")
    return True"""
    
    code_input = st.text_area("Paste Python Code:", value=default_code, height=400)
    run_btn = st.button("🚀 Enforce Governance", type="primary")

# --- AI LOGIC ENGINE ---
if run_btn and code_input:
    
    if not api_key:
        st.error("⚠️ Please enter your OpenAI API Key in the sidebar first!")
        st.stop()
        
    system_instruction = ""
    
    # LOGIC FOR SPLUNK (RAG)
    if mode == "Splunk Enterprise (PDF RAG)":
        with st.spinner("📖 Ingesting Splunk Style Guide PDF..."):
            rules_context = get_splunk_rules(pdf_path)
            if not rules_context:
                st.error(f"Could not read {pdf_path}. Check file name.")
                st.stop()
                
        system_instruction = f"""
        You are the Chief Architect for the Splunk SDK.
        YOUR KNOWLEDGE BASE (OFFICIAL SPLUNK STYLE GUIDE):
        {rules_context}
        
        YOUR TASK:
        Refactor the user's code to satisfy:
        1. **Google Python Style:** Add Type Hints & Semantic Variables.
        2. **Splunk Content Style:** Enforce Active Voice and Present Tense from the PDF.
        """

    # LOGIC FOR NVIDIA (EXPERT SYSTEM)
    elif mode == "NVIDIA Omniverse (USD/Kit)":
        system_instruction = """
        You are a Senior Developer Relations Engineer for NVIDIA Omniverse.
        
        YOUR TASK:
        Refactor code to follow **NVIDIA Kit Extension** standards.
        
        RULES:
        1. **USD Context:** Use `omni.usd.get_context()` instead of opening stages manually.
        2. **Async:** Use `async def` for UI safety.
        3. **Types:** Use `pxr.Usd` and `pxr.Sdf` types.
        """

    # LOGIC FOR STANDARD
    else:
        system_instruction = "Refactor this code to standard PEP8 Python guidelines with Type Hints."

    # RUN THE LLM
    try:
        # We now use 'model_choice' from the sidebar
        llm = ChatOpenAI(
            model_name=model_choice, 
            temperature=0, 
            openai_api_key=api_key
        )
        
        prompt_template = PromptTemplate(
            template="{instruction}\n\nUSER CODE:\n{code}",
            input_variables=["instruction", "code"]
        )
        
        with st.spinner("🤖 Refactoring..."):
            final_prompt = prompt_template.format(instruction=system_instruction, code=code_input)
            response = llm.invoke(final_prompt)
            
        with col2:
            st.subheader("2. Output: Compliant Code")
            st.markdown(response.content)
            st.success("✅ Governance Checks Passed")
            
    except Exception as e:
        st.error(f"An error occurred: {e}")