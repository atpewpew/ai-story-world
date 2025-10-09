from typing import List, Dict, Any, Optional
import os
import time

try:
    import chromadb  # type: ignore
    from sentence_transformers import SentenceTransformer  # type: ignore
    import pinecone  # type: ignore
    import qdrant_client  # type: ignore
    from qdrant_client import QdrantClient  # type: ignore
except Exception:
    chromadb = None
    SentenceTransformer = None  # type: ignore
    pinecone = None
    qdrant_client = None
    QdrantClient = None


class _InMemoryVectorStore:
    def __init__(self) -> None:
        self._docs: List[Dict[str, Any]] = []

    def upsert(self, doc: Dict[str, Any]) -> None:
        self._docs.append(doc)

    def query(self, session_id: str, text: str, k: int = 6) -> List[str]:
        candidates = [d["text"] for d in self._docs if d.get("session_id") == session_id]
        return candidates[-k:]


class VectorStore:
    def __init__(self) -> None:
        self.backend: Optional[str] = None
        self.client = None
        self.collection = None
        self.encoder = None
        self._mem = _InMemoryVectorStore()
        
        # Determine backend from environment
        backend_preference = os.getenv("VECTOR_BACKEND", "chroma").lower()
        
        if backend_preference == "pinecone" and pinecone is not None:
            self._init_pinecone()
        elif backend_preference == "qdrant" and QdrantClient is not None:
            self._init_qdrant()
        elif chromadb is not None and SentenceTransformer is not None:
            self._init_chroma()
        else:
            self.backend = "memory"
    
    def _init_chroma(self):
        try:
            self.backend = "chroma"
            self.client = chromadb.Client()
            self.collection = self.client.get_or_create_collection("story_memories")
            model_name = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
            self.encoder = SentenceTransformer(model_name)
        except Exception:
            self.backend = "memory"
    
    def _init_pinecone(self):
        try:
            self.backend = "pinecone"
            api_key = os.getenv("PINECONE_API_KEY")
            environment = os.getenv("PINECONE_ENVIRONMENT", "us-west1-gcp")
            index_name = os.getenv("PINECONE_INDEX", "story-memories")
            
            pinecone.init(api_key=api_key, environment=environment)
            self.client = pinecone.Index(index_name)
            
            model_name = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
            self.encoder = SentenceTransformer(model_name)
        except Exception:
            self.backend = "memory"
    
    def _init_qdrant(self):
        try:
            self.backend = "qdrant"
            url = os.getenv("QDRANT_URL", "http://localhost:6333")
            api_key = os.getenv("QDRANT_API_KEY")
            
            self.client = QdrantClient(url=url, api_key=api_key)
            collection_name = os.getenv("QDRANT_COLLECTION", "story_memories")
            
            # Create collection if it doesn't exist
            try:
                self.client.get_collection(collection_name)
            except Exception:
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config={"size": 384, "distance": "Cosine"}
                )
            
            self.collection = collection_name
            
            model_name = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
            self.encoder = SentenceTransformer(model_name)
        except Exception:
            self.backend = "memory"

    def upsert(self, doc: Dict[str, Any]) -> None:
        if self.backend == "chroma" and self.collection is not None and self.encoder is not None:
            try:
                text = doc.get("text", "")
                sid = doc.get("session_id", "")
                did = doc.get("id") or f"{sid}-{doc.get('turn_id', int(time.time()))}"
                emb = self.encoder.encode([text]).tolist()[0]
                self.collection.upsert(ids=[did], embeddings=[emb], metadatas=[doc], documents=[text])
                return
            except Exception:
                pass
        self._mem.upsert(doc)

    def query(self, session_id: str, text: str, k: int = 6) -> List[str]:
        if self.backend == "chroma" and self.collection is not None and self.encoder is not None:
            try:
                emb = self.encoder.encode([text]).tolist()[0]
                res = self.collection.query(query_embeddings=[emb], n_results=k, where={"session_id": session_id})
                docs = res.get("documents") or [[]]
                return list(docs[0])
            except Exception:
                pass
        return self._mem.query(session_id, text, k)


_GLOBAL_STORE: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    global _GLOBAL_STORE
    if _GLOBAL_STORE is None:
        _GLOBAL_STORE = VectorStore()
    return _GLOBAL_STORE

