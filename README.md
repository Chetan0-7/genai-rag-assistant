# GenAI Chat Assistant (RAG)

A production-grade Document-Grounded Conversational AI Assistant using Retrieval-Augmented Generation (RAG).

## Features
- **Document Loading & Chunking:** Reads `docs.json` and splits text into chunks.
- **Embeddings & Vector Store:** Generates OpenAI embeddings and stores them in memory.
- **Similarity Search:** Cosine similarity via `numpy` to retrieve relevant context.
- **LLM Integration:** OpenAI GPT-3.5-Turbo grounded exclusively on retrieved context.
- **Conversation Memory:** Remembers the last 5 messages for continuity.
- **Modern UI:** Responsive, stylish frontend built with HTML, CSS, JavaScript.

## Setup Instructions

### 1. Requirements
Ensure you have Python 3.8+ installed.

### 2. Virtual Environment
Create and activate a virtual environment:
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. API Key Configuration
Create a `.env` file in the root directory (where `app.py` is located) and add your OpenAI API key:
```env
OPENAI_API_KEY=your_openai_api_key_here
```
Alternatively, set it in your terminal:
```bash
# Windows
set OPENAI_API_KEY=your_openai_api_key_here

# macOS / Linux
export OPENAI_API_KEY=your_openai_api_key_here
```

### 5. Run the Application
Start the Flask backend API:
```bash
python app.py
```

### 6. Access UI
Open your browser and navigate to: [http://localhost:5000](http://localhost:5000)
