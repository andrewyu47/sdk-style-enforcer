import streamlit as st
import os
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="SDK Style Enforcer",
    page_icon="🛡️",
    layout="wide"
)

# --- SIDEBAR (Configuration) ---
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # 1. API Key Input
    api_key = st.text_input("OpenAI API Key", type="password")
    if not api_key:
        st.warning("⚠️ Please enter your OpenAI API Key to proceed.")
        st.stop()
    
    # 2. Select Style Guide
    style_guide = st.selectbox(
        "Select Enforcement Standard",
        ["Google Python Style Guide", "NVIDIA Omniverse Extension Style", "PEP 8 Standard"]
    )
    
    # 3. Model Selection
    model_choice = st.selectbox("Select Model", ["gpt-3.5-turbo", "gpt-4"])
    
    st.markdown("---")
    st.markdown("**About this Tool**")
    st.markdown("This tool uses GenAI to act as a 'Linter-as-a-Service', refactoring messy code to meet strict developer ecosystem standards.")

# --- MAIN APP UI ---
st.title("🛡️ SDK Style Enforcer")
st.markdown(f"**Current Mode:** `{style_guide}`")

col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Input: Messy Code")
    # A default "messy" example for testing
    default_code = """def calc(x,y):
    # doing math
    z = x * y
    print(z)
    return z"""
    
    code_input = st.text_area("Paste undocumented/messy Python here:", value=default_code, height=400)
    
    analyze_btn = st.button("🚀 Enforce Standards", type="primary")

# --- AI LOGIC ---
if analyze_btn and code_input:
    # Set the Key
    os.environ["OPENAI_API_KEY"] = api_key
    
    # Define the Prompt (The "DevRel" Secret Sauce)
    template = """
    You are a Senior Staff Engineer and Developer Advocate at a major tech company.
    Your goal is to refactor the user's code to strictly follow the '{style}' standard.
    
    INSTRUCTIONS:
    1. REFACTOR the code to add Type Hints (typing module).
    2. ADD a Google-Style Docstring explaining args and returns.
    3. IMPROVE variable names to be semantic (e.g., change 'x' to 'price').
    4. GENERATE a Markdown explanation of what you changed and why.

    INPUT CODE:
    {code}

    OUTPUT FORMAT:
    [Provide the Refactored Python Code inside a code block]
    [Provide the "Why I Changed This" explanation in Markdown below it]
    """
    
    # Initialize the Chain
    llm = ChatOpenAI(model_name=model_choice, temperature=0)
    prompt = PromptTemplate(template=template, input_variables=["style", "code"])
    
    with st.spinner("🤖 AI is reviewing and refactoring..."):
        # Run the prompt
        formatted_prompt = prompt.format(style=style_guide, code=code_input)
        response = llm.invoke(formatted_prompt)
        result_text = response.content

    # --- DISPLAY RESULTS ---
    with col2:
        st.subheader("2. Output: Standardized Code")
        st.markdown(result_text)
        st.success("✅ Compliance Check Complete")