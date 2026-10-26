import os
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
import chromadb
from google import genai
from dotenv import load_dotenv

# Hugging Face Fallback Import
from transformers import pipeline

# Load environment variables
load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY")

# Initialize Google GenAI Client
client = genai.Client(api_key=api_key)

# Initialize local embedding model (Runs 100% free on CPU)
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# Initialize local vector database
chroma_client = chromadb.Client()
collection = chroma_client.get_or_create_collection(name="study_notes")

# Lazy-load Hugging Face fallback model (using a non-gated, lightweight model)
hf_generator = None
def get_hf_pipeline():
    global hf_generator
    if hf_generator is None:
        print("Loading open-access fallback model (Qwen/Qwen2.5-0.5B-Instruct)...")
        # Qwen2.5-0.5B-Instruct is completely open, non-gated, and instruction-tuned
        hf_generator = pipeline("text-generation", model="Qwen/Qwen2.5-0.5B-Instruct", device_map="auto")
    return hf_generator

def process_uploaded_file(uploaded_file):
    """Reads an uploaded PDF, splits it into chunks, and stores them in ChromaDB."""
    reader = PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        if page.extract_text():
            text += page.extract_text() + "\n"
            
    if not text.strip():
        return 0
        
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = text_splitter.split_text(text)
    
    embeddings = embedding_model.encode(chunks).tolist()
    ids = [f"chunk_{i}_{os.urandom(4).hex()}" for i in range(len(chunks))]
    
    collection.add(
        documents=chunks,
        embeddings=embeddings,
        ids=ids
    )
    return len(chunks)

def call_llm_with_fallback(prompt):
    """Tries Gemini first; if 503 or error occurs, falls back to open Hugging Face model."""
    gemini_models = ['gemini-1.5-flash', 'gemini-1.5-pro']
    
    for model_name in gemini_models:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt
            )
            if response and response.text:
                return response.text
        except Exception as e:
            print(f"Gemini model {model_name} failed: {e}. Trying next option...")
            continue
            
    # If all Gemini attempts fail, fallback to open Hugging Face model
    print("Falling back to local Hugging Face model...")
    try:
        generator = get_hf_pipeline()
        # Format prompt cleanly for instruction models
        messages = [{"role": "user", "content": prompt}]
        outputs = generator(messages, max_new_tokens=300, do_sample=True, temperature=0.3)
        # Extract response text
        generated_text = outputs[0]['generated_text']
        if isinstance(generated_text, list):
            return generated_text[-1]['content']
        return generated_text
    except Exception as hf_error:
        return f"Error: Both Gemini and Hugging Face fallback failed. Details: {hf_error}"

def ask_study_companion(question):
    """Retrieves relevant chunks and generates a grounded response."""
    if collection.count() == 0:
        return "Please upload and process some study notes first!", []
        
    q_embedding = embedding_model.encode([question]).tolist()
    results = collection.query(
        query_embeddings=q_embedding,
        n_results=min(3, collection.count())
    )
    retrieved_chunks = results['documents'][0]
    context = "\n---\n".join(retrieved_chunks)
    
    prompt = f"""
    You are an expert AI study companion. Answer the student's question strictly using the provided study notes context below. 
    If the answer cannot be found in the context, you must reply precisely with: 
    "The provided notes do not contain enough information to answer this question."
    
    Study Notes Context:
    {context}
    
    Student Question: {question}
    """
    
    answer = call_llm_with_fallback(prompt)
    return answer, retrieved_chunks

def generate_quiz():
    """Generates a practice quiz question from stored document chunks."""
    all_data = collection.get()
    if not all_data['documents']:
        return "Please upload notes first!"
    
    sample_text = all_data['documents'][0]
    
    prompt = f"""
    Based on this excerpt from the notes, generate 1 conceptual multiple-choice question, 
    including 4 options (A, B, C, D) and specify the correct answer:
    {sample_text}
    """
    return call_llm_with_fallback(prompt)

def evaluate_answer(question, student_answer):
    """Evaluates the student's answer and provides targeted feedback/hints."""
    prompt = f"""
    The quiz question / context was: {question}
    The student's submitted answer was: {student_answer}
    
    Evaluate the student's response. If correct, praise them and reinforce the concept. 
    If incorrect, explain why gently, point out the misunderstanding based on the notes, 
    and provide a guiding hint without just giving the direct answer away.
    """
    return call_llm_with_fallback(prompt)