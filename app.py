import streamlit as st
import os
from dotenv import load_dotenv
import time

# Import our custom modules
from connectors.gdrive import GDriveConnector
from processing.parser import DocumentParser
from processing.chunker import DocumentChunker
from embedding.model import EmbeddingModel
from search.vector_store import VectorStore
from api.llm_service import LLMService

load_dotenv()

# Page Config
st.set_page_config(page_title="Drive Intelligence", page_icon="🧠", layout="wide")

# Custom CSS for Premium Look
st.markdown("""
    <style>
    .stApp {
        background: #0E1117;
    }
    .main {
        background: radial-gradient(circle at top left, #1a1a2e, #0E1117);
    }
    div.stButton > button {
        background-color: #2E6BFF;
        color: white;
        border-radius: 10px;
        padding: 0.5rem 2rem;
        border: none;
        box-shadow: 0 4px 15px rgba(46, 107, 255, 0.3);
    }
    .source-tag {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.7rem;
        color: #888;
        margin-right: 5px;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize Session State
if 'initialized' not in st.session_state:
    try:
        # Load core AI components first (These don't need GDrive credentials)
        st.session_state.embedding_model = EmbeddingModel()
        st.session_state.vector_store = VectorStore()
        st.session_state.chunker = DocumentChunker()
        st.session_state.llm_service = LLMService()
        st.session_state.initialized = True
        
        # Try to load GDrive but don't crash if it fails (Important for live demo)
        try:
            st.session_state.connector = GDriveConnector()
            st.session_state.gdrive_ready = True
        except Exception:
            st.session_state.gdrive_ready = False
            
    except Exception as e:
        st.error(f"Critical initialization failed: {e}")
        st.session_state.initialized = False

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/300/300221.png", width=50)
    st.title("Settings")
    
    if not st.session_state.get('gdrive_ready', False):
        st.warning("⚠️ Live GDrive connection not active. Using pre-indexed knowledge base.")
        if st.button("Retry Connection", use_container_width=True):
            st.rerun()
    
    if st.button("🔄 Sync Google Drive", use_container_width=True, disabled=not st.session_state.get('gdrive_ready', False)):
        with st.status("Syncing Documents...", expanded=True) as status:
            try:
                st.write("Listing files...")
                files = st.session_state.connector.list_files()
                
                all_chunks = []
                progress_bar = st.progress(0)
                
                for i, file in enumerate(files):
                    st.write(f"Processing: {file['name']}")
                    try:
                        content = st.session_state.connector.download_file(file['id'], file['mimeType'])
                        text = DocumentParser.extract_text(content, file['mimeType'])
                        
                        metadata = {
                            "doc_id": file['id'],
                            "file_name": file['name'],
                            "source": "gdrive"
                        }
                        
                        chunks = st.session_state.chunker.chunk_text(text, metadata)
                        all_chunks.extend(chunks)
                    except Exception as e:
                        st.warning(f"Skipped {file['name']}: {e}")
                    
                    progress_bar.progress((i + 1) / len(files))

                if all_chunks:
                    st.write(f"Generating embeddings for {len(all_chunks)} chunks...")
                    texts = [c['text'] for c in all_chunks]
                    embeddings = st.session_state.embedding_model.generate_embeddings(texts)
                    
                    st.session_state.vector_store.add_documents(embeddings, all_chunks)
                    status.update(label="Sync Complete!", state="complete", expanded=False)
                    st.success(f"Indexed {len(all_chunks)} chunks from {len(files)} files.")
                else:
                    st.error("No chunks found to index.")
            except Exception as e:
                st.error(f"Sync failed: {e}")

    st.divider()
    st.subheader("Database Stats")
    if 'vector_store' in st.session_state:
        st.metric("Total Chunks", len(st.session_state.vector_store.chunks))
    
    st.info("Files supported: PDF, Google Docs, TXT")

# Main Chat Interface
st.title("🧠 Drive Intelligence")
st.caption("Grounded AI over your personal Google Drive documents.")

# Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "sources" in message:
            cols = st.columns(len(message["sources"]))
            for i, source in enumerate(message["sources"]):
                st.caption(f"📍 {source}")

# Query Input
if query := st.chat_input("Ask about your documents..."):
    # Add User Message
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    # Generate Response
    with st.chat_message("assistant"):
        if not st.session_state.vector_store.chunks:
            st.warning("Please sync your Google Drive first!")
        else:
            with st.spinner("Searching through documents..."):
                # 1. Embed query
                query_embedding = st.session_state.embedding_model.generate_embeddings(query)[0]
                
                # 2. Retrieve top chunks
                relevant_chunks = st.session_state.vector_store.search(query_embedding, k=5)
                
                if not relevant_chunks:
                    answer = "I couldn't find any relevant information in your Drive."
                    sources = []
                else:
                    # 3. Generate answer via LLM
                    answer = st.session_state.llm_service.generate_answer(query, relevant_chunks)
                    sources = list(set([c['metadata']['file_name'] for c in relevant_chunks]))

                st.markdown(answer)
                
                # Display Sources
                if sources:
                    st.divider()
                    st.write("**Sources:**")
                    for source in sources:
                        st.caption(f"📄 {source}")
                
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": answer,
                    "sources": sources
                })
