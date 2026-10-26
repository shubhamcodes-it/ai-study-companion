import streamlit as st
from utils import process_uploaded_file, ask_study_companion, generate_quiz, evaluate_answer
import asyncio
import sys

# Fixes the Windows Proactor event loop warning on browser refresh
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import streamlit as st
from utils import process_uploaded_file, ask_study_companion, generate_quiz, evaluate_answer
# ... rest of your code ...
st.set_page_config(page_title="Study Companion AI", page_icon="📚", layout="centered")

st.title("📚 Adaptive Learning & Knowledge Support Study Companion")
st.markdown("Turn your lecture notes into an interactive, grounded AI tutor that verifies evidence and tests your knowledge.")

# Sidebar for uploading notes
st.sidebar.header("1. Upload Study Material")
uploaded_file = st.sidebar.file_uploader("Upload lecture PDF", type=["pdf"])

if uploaded_file:
    if st.sidebar.button("Process & Vectorize Notes"):
        with st.spinner("Processing document chunks..."):
            try:
                num_chunks = process_uploaded_file(uploaded_file)
                if num_chunks > 0:
                    st.sidebar.success(f"Successfully processed {num_chunks} chunks!")
                else:
                    st.sidebar.error("No text could be extracted from this PDF.")
            except Exception as e:
                st.sidebar.error(f"Error processing file: {e}")

# Main Tabs for the Learning Flow
tab1, tab2 = st.tabs(["💬 Ask & Inspect Evidence", "📝 Practice Quiz"])

with tab1:
    st.header("Ask a Question from Your Notes")
    user_query = st.text_input("What would you like to clarify?")
    
    if user_query:
        with st.spinner("Searching notes and generating grounded answer..."):
            answer, evidence = ask_study_companion(user_query)
            
        st.markdown("### **AI Tutor Answer:**")
        st.write(answer)
        
        # Evidence Inspection Expander (Meets core demo requirements)
        if evidence:
            with st.expander("🔍 Inspect Supporting Evidence"):
                for i, chunk in enumerate(evidence):
                    st.markdown(f"**Source Excerpt {i+1}:**")
                    st.info(chunk)

with tab2:
    st.header("Interactive Practice Quiz")
    st.markdown("Test your understanding based on your uploaded study notes.")
    
    if st.button("Generate New Quiz Question"):
        with st.spinner("Generating question from notes..."):
            st.session_state['quiz'] = generate_quiz()
        st.session_state['feedback'] = ""
        
    if 'quiz' in st.session_state and st.session_state['quiz']:
        st.markdown("### **Question:**")
        st.write(st.session_state['quiz'])
        
        student_response = st.text_input("Your Answer / Explanation:", key="student_input")
        
        if st.button("Submit Answer"):
            if student_response:
                with st.spinner("Evaluating your response..."):
                    feedback = evaluate_answer(st.session_state['quiz'], student_response)
                st.markdown("### **Targeted Feedback:**")
                st.write(feedback)
            else:
                st.warning("Please type your answer before submitting.")