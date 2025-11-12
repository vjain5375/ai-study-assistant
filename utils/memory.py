"""Memory module using FAISS for semantic search and embeddings"""
import os
import pickle
import numpy as np
from typing import List, Dict, Tuple
import faiss
from sentence_transformers import SentenceTransformer
import config


class MemoryModule:
    """Memory module using FAISS for efficient semantic search"""
    
    def __init__(self):
        self.embedding_model = None
        self.index = None
        self.texts = []  # Store original texts
        self.metadata = []  # Store metadata for each text
        self.dimension = config.EMBEDDING_DIMENSION
        self.index_path = os.path.join(config.OUTPUT_DIR, "faiss_index.bin")
        self.metadata_path = os.path.join(config.OUTPUT_DIR, "faiss_metadata.pkl")
        
        # Initialize embedding model
        self._load_embedding_model()
        
        # Load or create FAISS index
        self._load_or_create_index()
    
    def _load_embedding_model(self):
        """Load the embedding model (bge-large)"""
        try:
            print(f"Loading embedding model: {config.EMBEDDING_MODEL}")
            self.embedding_model = SentenceTransformer(config.EMBEDDING_MODEL)
            print("Embedding model loaded successfully")
        except Exception as e:
            print(f"Error loading embedding model: {e}")
            print("Falling back to a smaller model...")
            try:
                # Fallback to a smaller model
                self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                self.dimension = 384  # Update dimension for fallback model
            except Exception as e2:
                raise Exception(f"Could not load any embedding model: {e2}")
    
    def _load_or_create_index(self):
        """Load existing FAISS index or create a new one"""
        if os.path.exists(self.index_path) and os.path.exists(self.metadata_path):
            try:
                # Load existing index
                self.index = faiss.read_index(self.index_path)
                with open(self.metadata_path, 'rb') as f:
                    data = pickle.load(f)
                    self.texts = data.get('texts', [])
                    self.metadata = data.get('metadata', [])
                print(f"Loaded existing FAISS index with {len(self.texts)} documents")
            except Exception as e:
                print(f"Error loading existing index: {e}. Creating new index...")
                self._create_new_index()
        else:
            self._create_new_index()
    
    def _create_new_index(self):
        """Create a new FAISS index"""
        # Use L2 distance (Euclidean) - common for embeddings
        self.index = faiss.IndexFlatL2(self.dimension)
        self.texts = []
        self.metadata = []
        print("Created new FAISS index")
    
    def add_documents(self, texts: List[str], metadata: List[Dict] = None):
        """
        Add documents to the memory index.
        
        Args:
            texts: List of text documents
            metadata: Optional list of metadata dictionaries
        """
        if not texts:
            return
        
        # Generate embeddings
        print(f"Generating embeddings for {len(texts)} documents...")
        embeddings = self.embedding_model.encode(texts, show_progress_bar=True, convert_to_numpy=True)
        
        # Normalize embeddings for better cosine similarity (optional)
        # faiss.normalize_L2(embeddings)
        
        # Add to index
        self.index.add(embeddings.astype('float32'))
        
        # Store texts and metadata
        self.texts.extend(texts)
        if metadata:
            self.metadata.extend(metadata)
        else:
            self.metadata.extend([{}] * len(texts))
        
        print(f"Added {len(texts)} documents to memory. Total: {len(self.texts)}")
        
        # Save index
        self.save()
    
    def search(self, query: str, k: int = 5) -> List[Tuple[str, float, Dict]]:
        """
        Search for similar documents.
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List of tuples: (text, distance, metadata)
        """
        if len(self.texts) == 0:
            return []
        
        # Generate query embedding
        query_embedding = self.embedding_model.encode([query], convert_to_numpy=True)
        
        # Search
        k = min(k, len(self.texts))  # Don't search for more than available
        distances, indices = self.index.search(query_embedding.astype('float32'), k)
        
        # Format results
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.texts):
                results.append((
                    self.texts[idx],
                    float(distances[0][i]),
                    self.metadata[idx]
                ))
        
        return results
    
    def find_relevant_chunks(self, query: str, chunks: List[str], k: int = 3) -> List[str]:
        """
        Find most relevant chunks for a query using semantic search.
        
        Args:
            query: Search query
            chunks: List of text chunks
            k: Number of chunks to return
            
        Returns:
            List of most relevant chunks
        """
        if not chunks:
            return []
        
        # If index is empty or small, add chunks temporarily
        if len(self.texts) < len(chunks):
            # Add chunks to index if not already there
            self.add_documents(chunks)
        
        # Search for relevant chunks
        results = self.search(query, k=k)
        
        # Return texts in order of relevance
        return [text for text, _, _ in results]
    
    def save(self):
        """Save the FAISS index and metadata"""
        if not os.path.exists(config.OUTPUT_DIR):
            os.makedirs(config.OUTPUT_DIR)
        
        try:
            faiss.write_index(self.index, self.index_path)
            with open(self.metadata_path, 'wb') as f:
                pickle.dump({
                    'texts': self.texts,
                    'metadata': self.metadata
                }, f)
            print(f"Saved FAISS index to {self.index_path}")
        except Exception as e:
            print(f"Error saving FAISS index: {e}")
    
    def clear(self):
        """Clear all documents from memory"""
        self._create_new_index()
        if os.path.exists(self.index_path):
            os.remove(self.index_path)
        if os.path.exists(self.metadata_path):
            os.remove(self.metadata_path)
        print("Memory cleared")

