import os
import json
import threading
import numpy as np
from flask import Flask, request, jsonify, render_template
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Load explicitly from .env file if present
load_dotenv()

app = Flask(__name__)

# Initialize Gemini client. Depends on GEMINI_API_KEY environment variable.
client = None
api_key = os.environ.get("GEMINI_API_KEY")

if api_key:
    client = genai.Client(api_key=api_key)
else:
    print("WARNING: GEMINI_API_KEY not found in environment.")

# In-memory vector database
vector_db = []
# In-memory conversation memory (last 5 messages)
conversation_memory = []

def chunk_text(text, max_chars=300):
    """Split text into smaller chunks for embeddings."""
    words = text.split()
    chunks = []
    current_chunk = []
    current_length = 0
    
    for word in words:
        if current_length + len(word) > max_chars:
            chunks.append(" ".join(current_chunk))
            current_chunk = [word]
            current_length = len(word)
        else:
            current_chunk.append(word)
            current_length += len(word) + 1
            
    if current_chunk:
        chunks.append(" ".join(current_chunk))
        
    return chunks

def generate_embedding(text):
    """Generate vector embeddings using Gemini."""
    if not client: return None
    try:
        response = client.models.embed_content(
            model="gemini-embedding-001",
            contents=text,
        )
        return response.embeddings[0].values
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return None

def cosine_similarity(vec1, vec2):
    """Calculate cosine similarity between two vectors."""
    a = np.array(vec1)
    b = np.array(vec2)
    if np.linalg.norm(a) == 0 or np.linalg.norm(b) == 0:
        return 0.0
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def find_similar_chunks(query_embedding, top_k=3):
    """Retrieve top_k most similar chunks from the vector database."""
    scored_chunks = []
    for item in vector_db:
        score = cosine_similarity(query_embedding, item["embedding"])
        scored_chunks.append((score, item["chunk"]))
    
    # Sort by descending score
    scored_chunks.sort(key=lambda x: x[0], reverse=True)
    return [chunk for score, chunk in scored_chunks[:top_k]]

def initialize_knowledge_base():
    """Load docs.json, chunk them, and generate embeddings."""
    if not os.path.exists("docs.json"):
        print("docs.json not found. Skipping initialization.")
        return
        
    try:
        with open("docs.json", "r", encoding="utf-8") as f:
            docs = json.load(f)
            
        for doc in docs:
            text = f"Title: {doc.get('title', '')}\nContent: {doc.get('content', '')}"
            chunks = chunk_text(text)
            for chunk in chunks:
                embedding = generate_embedding(chunk)
                if embedding:
                    vector_db.append({
                        "chunk": chunk,
                        "embedding": embedding
                    })
        print(f"Knowledge base initialized with {len(vector_db)} chunks.")
    except Exception as e:
        print(f"Failed to load docs.json: {e}")

# Initialize the DB gracefully in the background so it doesn't block Gunicorn boot
if client:
    print("Starting knowledge base initialization...")
    threading.Thread(target=initialize_knowledge_base, daemon=True).start()
else:
    print("WARNING: GEMINI_API_KEY not found in environment. Please set it to enable RAG.")

@app.route("/health")
def health():
    return jsonify({"status": "healthy", "chunks_loaded": len(vector_db)}), 200

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_message = data.get("message", "").strip()
    
    if not user_message:
        return jsonify({"error": "Empty message."}), 400
        
    if not client:
         return jsonify({"response": "I cannot answer right now. Gemini API key is missing. Please set it up in the environment or .env file."})
        
    # 1. Generate Query Embedding
    query_embedding = generate_embedding(user_message)
    if not query_embedding:
        return jsonify({"response": "Error generating query embedding."}), 500
        
    # 2. Retrieve Similar Chunks (Context)
    similar_chunks = find_similar_chunks(query_embedding)
    context_text = "\n\n".join(similar_chunks)
    
    # 3. Build Prompt with Memory
    system_prompt = (
        "You are a helpful AI assistant. Answer the user's question using ONLY the provided context.\n"
        "If you cannot answer the question based on the context, say 'I don't know based on the provided documents.'"
    )
    
    # We will build a list of parts for the current message since Gemini expects a user prompt.
    # To include memory, we can embed it into a single structured prompt or use Gemini's ChatSession.
    # For simplicity matching the existing logic, we structure a single enriched prompt.
    
    prompt_parts = []
    
    # Add system instructions at the top
    prompt_parts.append(f"System Instructions:\n{system_prompt}\n")
    
    if conversation_memory:
        prompt_parts.append("--- Previous Conversation History ---")
        for msg in conversation_memory:
            prompt_parts.append(f"{msg['role'].capitalize()}: {msg['content']}")
        prompt_parts.append("---------------------------------------\n")
        
    # Construct formatting as requested
    prompt_parts.append(f"Context:\n{context_text}\n\nUser Question:\n{user_message}")
    
    final_prompt = "\n".join(prompt_parts)
    
    # 4. LLM Generation
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=final_prompt,
            config=types.GenerateContentConfig(
                temperature=0.3,
            )
        )
        assistant_reply = response.text
        
        # 5. Update Memory
        conversation_memory.append({"role": "user", "content": user_message})
        conversation_memory.append({"role": "assistant", "content": assistant_reply})
        
        # Keep only the last 5 user-assistant exchanges (10 messages total)
        if len(conversation_memory) > 10:
            conversation_memory.pop(0)
            conversation_memory.pop(0)
            
        return jsonify({"response": assistant_reply})
        
    except Exception as e:
        return jsonify({"response": f"Error communicating with LLM: {str(e)}"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
