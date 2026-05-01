import streamlit as st
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

# Page Config
st.set_page_config(page_title="Drive Intelligence", page_icon="🧠", layout="centered")

# Custom CSS for a clean, professional look
st.markdown("""
    <style>
    .stApp { background: #0E1117; }
    div.stButton > button {
        background-color: #2E6BFF;
        color: white;
        border-radius: 8px;
        border: none;
        width: 100%;
    }
    .stChatMessage { border-radius: 15px; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

# Initialize Session State
if 'initialized' not in st.session_state:
    try:
        st.session_state.connector = GDriveConnector()
        st.session_state.embedding_model = EmbeddingModel()
        st.session_state.vector_store = VectorStore()
        st.session_state.chunker = DocumentChunker()
        st.session_state.llm_service = LLMService()
        st.session_state.initialized = True
    except Exception as e:
        st.session_state.initialized = False

# Sidebar (Minimal)
with st.sidebar:
    st.title("🧠 Intelligence")
    if st.button("🔄 Sync Documents"):
        with st.status("Reading your Drive...", expanded=False) as status:
            try:
                files = st.session_state.connector.list_files()
                all_chunks = []
                for file in files:
                    try:
                        content = st.session_state.connector.download_file(file['id'], file['mimeType'])
                        text = DocumentParser.extract_text(content, file['mimeType'])
                        chunks = st.session_state.chunker.chunk_text(text, {"file_name": file['name']})
                        all_chunks.extend(chunks)
                    except: continue

                if all_chunks:
                    embeddings = st.session_state.embedding_model.generate_embeddings([c['text'] for c in all_chunks])
                    st.session_state.vector_store.add_documents(embeddings, all_chunks)
                    st.success(f"Synchronized {len(files)} files.")
                status.update(label="System Updated", state="complete")
            except Exception as e:
                st.error("Sync failed. Check credentials.")

# Main Chat
st.title("Drive Intelligence")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if query := st.chat_input("Ask anything about your drive..."):
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        if not st.session_state.vector_store.chunks:
            st.warning("Please sync your documents first.")
        else:
            with st.spinner("Processing..."):
                query_embedding = st.session_state.embedding_model.generate_embeddings(query)[0]
                relevant_chunks = st.session_state.vector_store.search(query_embedding, k=5)
                
                if relevant_chunks:
                    answer = st.session_state.llm_service.generate_answer(query, relevant_chunks)
                    sources = list(set([c['metadata']['file_name'] for c in relevant_chunks]))
                    st.markdown(answer)
                    st.caption(f"Sources: {', '.join(sources)}")
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                else:
                    st.write("I couldn't find any relevant data.")
