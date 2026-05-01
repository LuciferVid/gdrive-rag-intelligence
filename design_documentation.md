# Problem Framing & Workflow Design: GDrive Intelligence

## 1. Problem Framing

### The Pain Point
Users often store vast amounts of critical information (policy docs, research, case studies, GTM plans) in Google Drive. However, as the volume of documents grows, retrieving specific knowledge becomes a "needle in a haystack" problem. Traditional keyword search often fails to capture the semantic meaning or synthesize information across multiple documents.

### The Solution: "Personal ChatGPT over Google Drive"
A Retrieval-Augmented Generation (RAG) system that transforms siloed documents into an active knowledge base. By combining semantic search with Large Language Models (LLMs), we provide:
- **Instant Answers**: Users get direct answers instead of a list of files.
- **Cross-Document Synthesis**: The AI can synthesize insights from multiple PDFs and Docs simultaneously.
- **Grounded Truth**: Every answer is backed by internal documents, reducing LLM hallucinations.

---

## 2. Workflow Design

The system follows a 5-stage architectural pipeline:

### Stage 1: Data Ingestion (The Connector)
- **Mechanism**: OAuth 2.0 for secure, user-approved access.
- **Logic**: Filters for specific MIME types (`PDF`, `Google Docs`, `Plain Text`).
- **Optimization**: Google Docs are exported as `text/plain` on-the-fly to ensure uniform processing.

### Stage 2: Document Processing (The Parser)
- **Parsing**: `PyPDF2` extracts raw text from PDF layouts.
- **Chunking**: Uses a **Recursive Character Splitter**.
    - **Chunk Size**: 1000 characters.
    - **Overlap**: 200 characters (ensures semantic continuity across chunks).
- **Metadata**: Each chunk is tagged with `doc_id`, `file_name`, and `source` for downstream citation.

### Stage 3: Embedding Layer (The Knowledge Base)
- **Model**: `all-MiniLM-L6-v2` (SentenceTransformers).
- **Rationale**: Chosen for its high performance-to-latency ratio, making it ideal for real-time local processing.
- **Output**: Transforms 1000-char text chunks into 384-dimensional dense vectors.

### Stage 4: Search & Retrieval (The Intelligence)
- **Storage**: `FAISS` (Facebook AI Similarity Search).
- **Search Type**: L2 Distance (Euclidean) for finding the closest semantic matches to the user's query.
- **Retrieval**: Fetches the top 5 most relevant chunks to serve as context for the LLM.

### Stage 5: Answer Layer (The Synthesis)
- **Model**: `Gemini 1.5 Flash`.
- **System Prompt**: Enforces strict grounding—if the answer isn't in the provided chunks, the AI must admit it doesn't know.
- **Output**: Returns a structured answer with a clear list of source documents used.

---

## 3. Technical Decisions & Rationale

| Decision | Selection | Rationale |
| :--- | :--- | :--- |
| **Framework** | FastAPI / Streamlit | FastAPI for the core logic; Streamlit for a premium, interactive user experience. |
| **Vector DB** | FAISS | Lightweight, local, and extremely fast. Perfect for "Personal" drive use cases without needing a complex cloud DB setup. |
| **LLM** | Gemini 1.5 Flash | Offers a massive context window and superior reasoning for grounded tasks compared to other free-tier alternatives. |
| **Auth** | OAuth 2.0 | Prioritizes user security. No need for users to handle complex Service Account JSONs manually. |

---

## 4. Scalability & Future Improvements
1. **Incremental Sync**: Implementing a "Last Updated" check to only process new or modified files.
2. **Hybrid Search**: Combining Keyword (BM25) and Semantic search for better accuracy on technical terms.
3. **Multimodal RAG**: Utilizing Gemini's vision capabilities to parse images and charts within PDFs.
