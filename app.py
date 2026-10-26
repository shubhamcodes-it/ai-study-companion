import asyncio
import sys

# Fixes Windows Proactor event loop warning on browser refresh
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import streamlit as st
from utils import process_uploaded_file, ask_study_companion, generate_quiz, evaluate_answer

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Study Companion AI | Hackathon Project", 
    page_icon="🎓", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS STYLING FOR HACKATHON POLISH ---
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #ffffff;
        border-radius: 6px;
        padding: 10px 20px;
        font-weight: 600;
        border: 1px solid #e0e0e0;
    }
    .stTabs [aria-selected="true"] {
        background-color: #ff4b4b !important;
        color: white !important;
    }
    .metric-card {
        background: white;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# --- SESSION STATE INITIALIZATION ---
if "processed_chunks" not in st.session_state:
    st.session_state["processed_chunks"] = 0
if "quiz" not in st.session_state:
    st.session_state["quiz"] = ""

# --- SIDEBAR: DOCUMENT UPLOAD & STATUS ---
with st.sidebar:
    st.image("https://img.icons8.com/color/96/artificial-intelligence.png", width=70)
    st.title("Study Companion")
    st.markdown("---")
    
    st.header("📂 1. Upload Material")
    uploaded_file = st.file_uploader("Upload lecture notes (PDF)", type=["pdf"])

    if uploaded_file:
        if st.button("🚀 Process & Vectorize Notes", type="primary", use_container_width=True):
            with st.spinner("Analyzing document chunks..."):
                try:
                    num_chunks = process_uploaded_file(uploaded_file)
                    if num_chunks > 0:
                        st.session_state["processed_chunks"] = num_chunks
                        st.success(f"Indexed {num_chunks} text chunks successfully!")
                    else:
                        st.error("No text could be extracted from this PDF.")
                except Exception as e:
                    st.error(f"Error: {e}")

    st.markdown("---")
    st.header("📊 System Metrics")
    st.metric(label="Indexed Knowledge Chunks", value=st.session_state["processed_chunks"])
    st.metric(label="RAG Vector Engine", value="ChromaDB (Active)")
    st.metric(label="AI Model Engine", value="Gemini / Qwen Fallback")
    
    st.markdown("---")
    st.caption("🏆 Hackathon Project Demo | Built with Streamlit & Python")

# --- MAIN HEADER ---
st.title("🎓 Adaptive Learning & Knowledge Support")
st.markdown("### *Turn static lecture notes into an interactive, grounded AI tutor with verifiable evidence.*")
st.markdown("---")

# --- NAVIGATION TABS ---
tab1, tab2, tab3 = st.tabs([
    "📖 Project Overview & Mission", 
    "💬 Smart Tutor & Evidence Inspector", 
    "📝 Interactive Practice Quiz"
])

# =========================================================================
# TAB 1: PROJECT OVERVIEW & MISSION (Ideal for Judges / Presentation)
# =========================================================================
with tab1:
    st.header("Welcome to the AI Study Companion")
    st.markdown("This application solves the core challenges students face during revision: **information overload** and **AI hallucinations**.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 🚨 The Problem Background
        * **Static Notes:** Students revise from dense lectures, notes, and short PDFs that can be hard to interpret.
        * **AI Hallucinations:** Generic chatbots answer from their own pre-trained knowledge even when the answer is absent from the study material.
        * **Lack of Verification:** Learners struggle to identify what they truly understand versus what is supported by their notes.
        """)
        
    with col2:
        st.markdown("""
        ### ✨ Our Solution & Features
        * **Strict RAG Grounding:** Answers are generated *strictly* using the user's uploaded notes.
        * **Evidence Inspection:** Every answer comes with expandable source quotes from your document.
        * **Unsupported Question Handling:** If notes lack the info, the system explicitly declines to guess.
        * **Adaptive Practice Quiz:** Automatically generates targeted questions and constructive feedback.
        """)
        
    st.markdown("---")
    st.subheader("⚙️ System Architecture & Workflow")
    st.info("Upload your notes in the sidebar -> Ask questions or test yourself in the tabs above!")

# =========================================================================
# TAB 2: SMART TUTOR & EVIDENCE INSPECTOR
# =========================================================================
with tab2:
    st.header("💬 Ask Questions & Inspect Supporting Evidence")
    st.markdown("Ask anything about your uploaded notes. The AI will retrieve the exact context and answer with citations.")
    
    user_query = st.text_input("What concept would you like to clarify from your notes?", placeholder="e.g., What is the primary mechanism of...")
    
    if user_query:
        if st.session_state["processed_chunks"] == 0:
            st.warning("⚠️ Please upload and process a PDF in the sidebar first!")
        else:
            with st.spinner("Searching knowledge base & generating grounded response..."):
                answer, evidence = ask_study_companion(user_query)
                
            # Display Answer in a clean card
            st.markdown("### 🤖 AI Tutor Response:")
            st.success(answer)
            
            # Evidence Inspection Expander (Meets core demo requirements)
            if evidence:
                with st.expander("🔍 Inspect Supporting Source Evidence (Click to expand)"):
                    for i, chunk in enumerate(evidence):
                        st.markdown(f"**Source Excerpt {i+1}:**")
                        st.info(chunk)

# =========================================================================
# TAB 3: INTERACTIVE PRACTICE QUIZ
# =========================================================================
with tab3:
    st.header("📝 Knowledge Check & Practice Quiz")
    st.markdown("Test your understanding based on the material you uploaded.")
    
    col_btn, col_spacer = st.columns([1, 2])
    with col_btn:
        if st.button("🎲 Generate Quiz Question", type="primary", use_container_width=True):
            if st.session_state["processed_chunks"] == 0:
                st.warning("Please upload notes first!")
            else:
                with st.spinner("Generating conceptual question from your notes..."):
                    st.session_state['quiz'] = generate_quiz()
                    
    if st.session_state['quiz']:
        st.markdown("---")
        st.markdown("### **🎯 Challenge Question:**")
        st.write(st.session_state['quiz'])
        
        student_response = st.text_input("Type your answer or explanation here:", key="quiz_input")
        
        if st.button("Submit & Get Feedback", type="secondary"):
            if student_response:
                with st.spinner("Evaluating your response..."):
                    feedback = evaluate_answer(st.session_state['quiz'], student_response)
                st.markdown("### **💡 Targeted Feedback & Guidance:**")
                st.info(feedback)
            else:
                st.warning("Please type your answer before submitting.")