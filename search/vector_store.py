import faiss
import numpy as np
import pickle
import os

class VectorStore:
    def __init__(self, index_path='data/vector_store/index.faiss', chunks_path='data/vector_store/chunks.pkl'):
        self.index_path = index_path
        self.chunks_path = chunks_path
        self.dimension = 384  # Dimension for all-MiniLM-L6-v2
        self.index = self._load_index()
        self.chunks = self._load_chunks()

    def _load_index(self):
        if os.path.exists(self.index_path):
            return faiss.read_index(self.index_path)
        return faiss.IndexFlatL2(self.dimension)

    def _load_chunks(self):
        if os.path.exists(self.chunks_path):
            with open(self.chunks_path, 'rb') as f:
                return pickle.load(f)
        return []

    def add_documents(self, embeddings, chunks):
        """Adds embeddings and corresponding chunks to the store."""
        self.index.add(np.array(embeddings).astype('float32'))
        self.chunks.extend(chunks)
        self.save()

    def search(self, query_embedding, k=5):
        """Searches for top k relevant chunks."""
        distances, indices = self.index.search(np.array([query_embedding]).astype('float32'), k)
        
        results = []
        for idx in indices[0]:
            if idx != -1 and idx < len(self.chunks):
                results.append(self.chunks[idx])
        return results

    def save(self):
        """Persists the index and chunks to disk."""
        faiss.write_index(self.index, self.index_path)
        with open(self.chunks_path, 'wb') as f:
            pickle.dump(self.chunks, f)

    def clear(self):
        """Clears the store."""
        self.index = faiss.IndexFlatL2(self.dimension)
        self.chunks = []
        if os.path.exists(self.index_path):
            os.remove(self.index_path)
        if os.path.exists(self.chunks_path):
            os.remove(self.chunks_path)
