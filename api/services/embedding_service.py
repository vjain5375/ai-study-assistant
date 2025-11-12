"""
Embedding Service for FAISS and Pinecone Integration
Handles vector embeddings and similarity search
"""
import os
import pickle
import numpy as np
from typing import List, Dict, Tuple, Optional
import faiss
from sentence_transformers import SentenceTransformer
import config


class EmbeddingService:
    """Service for managing embeddings and vector search"""
    
    def __init__(self, use_pinecone: bool = False, pinecone_api_key: str = None):
        """
        Initialize embedding service
        
        Args:
            use_pinecone: Whether to use Pinecone (default: FAISS)
            pinecone_api_key: Pinecone API key if using Pinecone
        """
        self.use_pinecone = use_pinecone
        self.embedding_model = None
        self.faiss_index = None
        self.texts = []
        self.metadata = []
        self.dimension = config.EMBEDDING_DIMENSION
        self.index_path = os.path.join(config.OUTPUT_DIR, "faiss_index.bin")
        self.metadata_path = os.path.join(config.OUTPUT_DIR, "faiss_metadata.pkl")
        
        # Initialize embedding model
        self._load_embedding_model()
        
        # Initialize vector store
        if use_pinecone:
            self._init_pinecone(pinecone_api_key)
        else:
            self._load_or_create_faiss_index()
    
    def _load_embedding_model(self):
        """Load the embedding model"""
        try:
            print(f"Loading embedding model: {config.EMBEDDING_MODEL}")
            self.embedding_model = SentenceTransformer(config.EMBEDDING_MODEL)
            print("✅ Embedding model loaded")
        except Exception as e:
            print(f"⚠️ Error loading model {config.EMBEDDING_MODEL}: {e}")
            print("Falling back to all-MiniLM-L6-v2...")
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            self.dimension = 384
    
    def _load_or_create_faiss_index(self):
        """Load existing FAISS index or create new one"""
        if os.path.exists(self.index_path) and os.path.exists(self.metadata_path):
            try:
                self.faiss_index = faiss.read_index(self.index_path)
                with open(self.metadata_path, 'rb') as f:
                    data = pickle.load(f)
                    self.texts = data.get('texts', [])
                    self.metadata = data.get('metadata', [])
                print(f"✅ Loaded FAISS index with {len(self.texts)} vectors")
            except Exception as e:
                print(f"⚠️ Error loading index: {e}. Creating new index...")
                self._create_faiss_index()
        else:
            self._create_faiss_index()
    
    def _create_faiss_index(self):
        """Create a new FAISS index"""
        self.faiss_index = faiss.IndexFlatL2(self.dimension)
        self.texts = []
        self.metadata = []
        print("✅ Created new FAISS index")
    
    def _init_pinecone(self, api_key: str):
        """Initialize Pinecone (if enabled)"""
        if not api_key:
            raise ValueError("Pinecone API key required when use_pinecone=True")
        
        try:
            import pinecone
            pinecone.init(api_key=api_key, environment="us-east1-gcp")
            # Create or connect to index
            index_name = "study-assistant"
            if index_name not in pinecone.list_indexes():
                pinecone.create_index(index_name, dimension=self.dimension)
            self.pinecone_index = pinecone.Index(index_name)
            print("✅ Pinecone initialized")
        except ImportError:
            raise ImportError("pinecone-client not installed. Install with: pip install pinecone-client")
    
    def create_embeddings(self, texts: List[str], show_progress: bool = True) -> np.ndarray:
        """
        Create embeddings for a list of texts
        
        Args:
            texts: List of text strings
            show_progress: Whether to show progress bar
            
        Returns:
            Numpy array of embeddings
        """
        if not texts:
            return np.array([])
        
        embeddings = self.embedding_model.encode(
            texts,
            show_progress_bar=show_progress,
            convert_to_numpy=True
        )
        return embeddings.astype('float32')
    
    def add_vectors(self, texts: List[str], metadata: List[Dict] = None, 
                   embedding_ids: List[str] = None, namespace: str = "default"):
        """
        Add vectors to the index with proper metadata linking
        
        Args:
            texts: List of text strings
            metadata: Optional metadata for each text (must include segment_id, file_id)
            embedding_ids: Optional IDs for embeddings
            namespace: Namespace/collection name (for Pinecone)
        """
        import logging
        logger = logging.getLogger(__name__)
        
        if not texts:
            logger.warning("embeddings: no texts provided for upsert")
            return
        
        logger.debug(f"embeddings: creating embeddings for {len(texts)} texts")
        
        # Create embeddings
        embeddings = self.create_embeddings(texts, show_progress=True)
        
        if self.use_pinecone:
            # Add to Pinecone with namespace
            vectors = []
            for i, (text, emb) in enumerate(zip(texts, embeddings)):
                vector_id = embedding_ids[i] if embedding_ids else f"vec_{i}"
                meta = metadata[i] if metadata else {}
                meta['text'] = text
                # Ensure required metadata fields
                if 'segment_id' not in meta:
                    meta['segment_id'] = meta.get('segment_id', f"seg_{i}")
                if 'file_id' not in meta:
                    meta['file_id'] = meta.get('file_id', 0)
                vectors.append((vector_id, emb.tolist(), meta))
            
            self.pinecone_index.upsert(vectors=vectors, namespace=namespace)
            logger.debug(f"embeddings: upserted {len(vectors)} vectors to Pinecone namespace={namespace}")
            
            # Verify upsert by querying count
            try:
                stats = self.pinecone_index.describe_index_stats()
                total_vectors = stats.get('total_vector_count', 0)
                logger.debug(f"embeddings: Pinecone total vectors={total_vectors} in namespace={namespace}")
            except Exception as e:
                logger.warning(f"embeddings: could not verify Pinecone count: {str(e)}")
        else:
            # Add to FAISS
            start_idx = len(self.texts)
            self.faiss_index.add(embeddings)
            self.texts.extend(texts)
            if metadata:
                self.metadata.extend(metadata)
            else:
                self.metadata.extend([{}] * len(texts))
            
            # Save index
            self.save_faiss_index()
            
            # Verify by checking index size
            index_size = self.faiss_index.ntotal
            logger.debug(f"embeddings: upserted {len(texts)} vectors to FAISS, total index size={index_size}")
            
            if index_size < start_idx + len(texts):
                logger.warning(f"embeddings: index size mismatch: expected >= {start_idx + len(texts)}, got {index_size}")
        
        logger.info(f"embeddings: successfully added {len(texts)} vectors to index")
    
    def search(self, query: str, k: int = 5, filter_dict: Dict = None, 
               file_id: int = None, namespace: str = "default") -> List[Tuple[str, float, Dict]]:
        """
        Search for similar vectors with document filtering
        
        Args:
            query: Search query text
            k: Number of results to return
            filter_dict: Optional metadata filter (Pinecone only)
            file_id: Optional file_id to filter results
            namespace: Namespace/collection name (for Pinecone)
            
        Returns:
            List of tuples: (text, distance/score, metadata)
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # Create query embedding
        logger.debug(f"retrieval: creating query embedding for query='{query[:50]}...', top_k={k}")
        query_embedding = self.create_embeddings([query], show_progress=False)[0]
        
        if self.use_pinecone:
            # Build filter with file_id if provided
            if file_id:
                if filter_dict:
                    filter_dict['file_id'] = file_id
                else:
                    filter_dict = {'file_id': file_id}
            
            # Search Pinecone
            results = self.pinecone_index.query(
                vector=query_embedding.tolist(),
                top_k=k,
                include_metadata=True,
                filter=filter_dict,
                namespace=namespace
            )
            
            results_list = []
            for match in results.matches:
                text = match.metadata.get('text', '')
                score = match.score
                metadata = {k: v for k, v in match.metadata.items() if k != 'text'}
                # Filter by file_id if provided and not in metadata
                if file_id and metadata.get('file_id') != file_id:
                    continue
                results_list.append((text, 1.0 - score, metadata))  # Convert similarity to distance
            
            logger.debug(f"retrieval: Pinecone returned {len(results_list)} results for query, top_k={k}")
            return results_list
        else:
            # Search FAISS
            if len(self.texts) == 0:
                logger.warning("retrieval: FAISS index is empty")
                return []
            
            k = min(k, len(self.texts))
            distances, indices = self.faiss_index.search(
                query_embedding.reshape(1, -1),
                k
            )
            
            results = []
            for i, idx in enumerate(indices[0]):
                if idx < len(self.texts):
                    metadata = self.metadata[idx]
                    # Filter by file_id if provided
                    if file_id and metadata.get('file_id') != file_id:
                        continue
                    results.append((
                        self.texts[idx],
                        float(distances[0][i]),
                        metadata
                    ))
            
            logger.debug(f"retrieval: FAISS returned {len(results)} results for query, top_k={k}")
            return results
    
    def retrieve_context(self, file_id: int, query: str = None, top_k: int = 6, 
                        namespace: str = "default") -> List[Dict]:
        """
        Retrieve context segments for RAG
        
        Args:
            file_id: Document ID to retrieve from
            query: Optional query for semantic search
            top_k: Number of segments to return
            namespace: Namespace for vector store
            
        Returns:
            List of segment dictionaries with text and metadata
        """
        import logging
        logger = logging.getLogger(__name__)
        
        if query:
            # Semantic search with query
            logger.debug(f"retrieval: semantic search for file_id={file_id}, query='{query[:50]}...', top_k={top_k}")
            search_results = self.search(
                query=query,
                k=top_k,
                file_id=file_id,
                namespace=namespace
            )
        else:
            # Retrieve top segments for document (by similarity to document summary)
            # For simplicity, we'll do a generic search or fetch by metadata
            logger.debug(f"retrieval: fetching top {top_k} segments for file_id={file_id}")
            # Use a generic query to get document segments
            search_results = self.search(
                query="document content",
                k=top_k * 2,  # Get more to filter
                file_id=file_id,
                namespace=namespace
            )
            # Take top_k
            search_results = search_results[:top_k]
        
        # Format results as segments
        segments = []
        for text, score, metadata in search_results:
            segments.append({
                'text': text,
                'score': score,
                'segment_id': metadata.get('segment_id'),
                'file_id': metadata.get('file_id', file_id),
                'topic': metadata.get('topic', ''),
                'chunk_index': metadata.get('chunk_index', 0)
            })
        
        logger.info(f"retrieval: returned {len(segments)} segments for file_id={file_id}")
        return segments
    
    def save_faiss_index(self):
        """Save FAISS index to disk"""
        if not self.use_pinecone and self.faiss_index:
            os.makedirs(config.OUTPUT_DIR, exist_ok=True)
            try:
                faiss.write_index(self.faiss_index, self.index_path)
                with open(self.metadata_path, 'wb') as f:
                    pickle.dump({
                        'texts': self.texts,
                        'metadata': self.metadata
                    }, f)
            except Exception as e:
                print(f"⚠️ Error saving FAISS index: {e}")

