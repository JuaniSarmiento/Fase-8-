"""
ChromaDB RAG Service - Vector Store for Context Retrieval
"""
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional
import os


class ChromaRAGService:
    """Service for RAG using ChromaDB vector store"""
    
    def __init__(self):
        """Initialize ChromaDB client"""
        self.chroma_host = os.getenv("CHROMA_HOST", "chromadb")
        self.chroma_port = int(os.getenv("CHROMA_PORT", "8000"))
        self.collection_name = os.getenv("CHROMA_COLLECTION_NAME", "ai_native_rag")
        self.available = False
        self.collection = None
        
        try:
            # Initialize client
            self.client = chromadb.HttpClient(
                host=self.chroma_host,
                port=self.chroma_port,
                settings=Settings(
                    anonymized_telemetry=False
                )
            )
            
            # Get or create collection
            try:
                self.collection = self.client.get_collection(name=self.collection_name)
            except:
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={"description": "AI-Native Learning Platform RAG"}
                )
            
            self.available = True
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"ChromaDB not available: {e}. RAG disabled.")
    
    def add_documents(
        self,
        documents: List[str],
        metadatas: List[Dict],
        ids: List[str]
    ) -> None:
        """Add documents to vector store"""
        if not self.available:
            return
        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
    
    def search(
        self,
        query: str,
        n_results: int = 3,
        filters: Optional[Dict] = None
    ) -> List[Dict]:
        """Search for relevant context"""
        if not self.available:
            return []
        
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=filters if filters else None
            )
        except Exception:
            return []
        
        # Format results
        contexts = []
        if results['documents'] and len(results['documents']) > 0:
            for i, doc in enumerate(results['documents'][0]):
                contexts.append({
                    'content': doc,
                    'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                    'distance': results['distances'][0][i] if results.get('distances') else 0
                })
        
        return contexts
    
    def get_context_for_topic(self, topic: str, language: str = "python") -> str:
        """Get relevant context for a programming topic"""
        contexts = self.search(
            query=f"{topic} {language} programming",
            n_results=3,
            filters={"language": language}
        )
        
        if not contexts:
            return ""
        
        # Combine contexts
        combined = "\n\n".join([ctx['content'] for ctx in contexts])
        return combined[:2000]  # Limit to 2000 chars
