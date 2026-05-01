# GDrive RAG Intelligence System

This system connects to your Google Drive, indexes your documents (PDFs, Google Docs, TXT), and allows you to ask questions about them using a Retrieval-Augmented Generation (RAG) pipeline.

## Architecture
- **Connectors**: Google Drive API integration via OAuth 2.0.
- **Processing**: Text extraction from PDFs and Google Docs with recursive chunking.
- **Embedding**: Local vectorization using `sentence-transformers` (`all-MiniLM-L6-v2`).
- **Search**: Vector similarity search using `FAISS`.
- **API**: FastAPI with asynchronous background synchronization.
- **LLM**: Google Gemini 1.5 Flash for grounded answer generation.

## Setup Instructions

### 1. Google Cloud Setup
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project.
3. Enable the **Google Drive API**.
4. Configure the **OAuth Consent Screen** (internal/external).
5. Create **OAuth 2.0 Client IDs** (Desktop App).
6. Download the JSON credentials and save them as `data/credentials/credentials.json`.

### 2. Environment Variables
Create a `.env` file in the root directory:
```env
GEMINI_API_KEY=your_gemini_api_key
GOOGLE_APPLICATION_CREDENTIALS=data/credentials/credentials.json
```

### 3. Installation
```bash
pip install -r requirements.txt
```

### 4. Running the Application
```bash
python -m api.main
```

## API Usage

### Sync Documents
Index your Google Drive documents:
```bash
curl -X POST http://localhost:8000/sync-drive
```

### Ask a Question
```bash
curl -X POST http://localhost:8000/ask \
     -H "Content-Type: application/json" \
     -d '{"query": "What are the company policies on remote work?"}'
```

## Tech Stack
- **Framework**: FastAPI
- **Embeddings**: SentenceTransformers
- **Vector DB**: FAISS
- **LLM**: Google Gemini
- **Auth**: Google OAuth 2.0
