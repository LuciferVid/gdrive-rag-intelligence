from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
import os
from dotenv import load_dotenv

# Import our custom modules
from connectors.gdrive import GDriveConnector
from processing.parser import DocumentParser
from processing.chunker import DocumentChunker
from embedding.model import EmbeddingModel
from search.vector_store import VectorStore
from api.llm_service import LLMService

load_dotenv()

app = FastAPI(title="GDrive RAG Intelligence")

# Global instances (lazy loaded or initialized on startup)
gdrive_connector = None
embedding_model = EmbeddingModel()
vector_store = VectorStore()
chunker = DocumentChunker()
llm_service = LLMService()

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    answer: str
    sources: List[str]

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def read_index():
    return FileResponse('static/index.html')

@app.on_event("startup")
async def startup_event():
    global gdrive_connector
    try:
        gdrive_connector = GDriveConnector()
    except Exception as e:
        print(f"Warning: GDrive Connector failed to initialize: {e}")

@app.post("/sync-drive")
async def sync_drive(background_tasks: BackgroundTasks):
    """Triggers the synchronization process from Google Drive."""
    if not gdrive_connector:
        raise HTTPException(status_code=500, detail="GDrive connector not initialized. Check credentials.")
    
    background_tasks.add_task(run_sync)
    return {"message": "Sync started in background."}

def run_sync():
    """Background task to sync files."""
    print("Starting Sync...")
    files = gdrive_connector.list_files()
    
    all_chunks = []
    # Note: For incremental sync, we would store file IDs and modifiedTimes in a DB
    # and only process files where modifiedTime > last_sync_time.
    for file in files:
        print(f"Processing: {file['name']}")
        try:
            content = gdrive_connector.download_file(file['id'], file['mimeType'])
            text = DocumentParser.extract_text(content, file['mimeType'])
            
            metadata = {
                "doc_id": file['id'],
                "file_name": file['name'],
                "source": "gdrive"
            }
            
            chunks = chunker.chunk_text(text, metadata)
            all_chunks.extend(chunks)
        except Exception as e:
            print(f"Error processing {file['name']}: {e}")

    if all_chunks:
        print(f"Generating embeddings for {len(all_chunks)} chunks...")
        texts = [c['text'] for c in all_chunks]
        embeddings = embedding_model.generate_embeddings(texts)
        
        vector_store.add_documents(embeddings, all_chunks)
        print("Sync Complete!")

@app.post("/ask", response_model=QueryResponse)
async def ask(request: QueryRequest):
    """Answers a question based on indexed documents."""
    if not vector_store.chunks:
        raise HTTPException(status_code=400, detail="No documents indexed. Run /sync-drive first.")
    
    # 1. Embed query
    query_embedding = embedding_model.generate_embeddings(request.query)[0]
    
    # 2. Retrieve top chunks
    relevant_chunks = vector_store.search(query_embedding, k=5)
    
    if not relevant_chunks:
        return QueryResponse(answer="I couldn't find any relevant information in your Drive.", sources=[])
    
    # 3. Generate answer via LLM
    answer = llm_service.generate_answer(request.query, relevant_chunks)
    
    # 4. Extract unique sources
    sources = list(set([c['metadata']['file_name'] for c in relevant_chunks]))
    
    return QueryResponse(answer=answer, sources=sources)

@app.get("/status")
async def status():
    return {
        "indexed_chunks": len(vector_store.chunks),
        "gdrive_connected": gdrive_connector is not None,
        "vector_store_path": vector_store.index_path
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
