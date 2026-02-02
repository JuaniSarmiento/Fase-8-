"""
ChromaVectorStore - Wrapper for ChromaDB compatible with LangGraph workflows
"""
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional, Any
import os
import logging

logger = logging.getLogger(__name__)


class ChromaVectorStore:
    """
    Vector store wrapper for ChromaDB with RAG capabilities
    
    Compatible with teacher_generator_graph and student_tutor_graph.
    """
    
    def __init__(
        self,
        persist_directory: str = "./chroma_data",
        host: Optional[str] = None,
        port: Optional[int] = None
    ):
        """
        Initialize ChromaDB client
        
        Args:
            persist_directory: Local directory for persistent storage
            host: Remote ChromaDB host (optional, for HTTP client)
            port: Remote ChromaDB port (optional)
        """
        self.persist_directory = persist_directory
        
        # Use HTTP client if host provided, otherwise use persistent client
        if host and port:
            self.client = chromadb.HttpClient(
                host=host,
                port=port,
                settings=Settings(anonymized_telemetry=False)
            )
            logger.info(f"ChromaDB HTTP client initialized: {host}:{port}")
        else:
            self.client = chromadb.PersistentClient(
                path=persist_directory,
                settings=Settings(anonymized_telemetry=False)
            )
            logger.info(f"ChromaDB persistent client initialized: {persist_directory}")
    
    def add_documents(
        self,
        documents: List[Dict[str, Any]],
        collection_name: str
    ) -> None:
        """
        Add documents to vector store
        
        Args:
            documents: List of dicts with 'content', 'metadata', 'id'
            collection_name: Name of the collection
        """
        try:
            # Get or create collection
            try:
                collection = self.client.get_collection(name=collection_name)
            except Exception:
                collection = self.client.create_collection(
                    name=collection_name,
                    metadata={"description": f"Collection for {collection_name}"}
                )
            
            # Extract data from documents
            doc_texts = []
            doc_metadatas = []
            doc_ids = []
            
            for i, doc in enumerate(documents):
                doc_texts.append(doc.get("content", ""))
                doc_metadatas.append(doc.get("metadata", {}))
                doc_ids.append(doc.get("id", f"{collection_name}_{i}"))
            
            # Add to collection
            collection.add(
                documents=doc_texts,
                metadatas=doc_metadatas,
                ids=doc_ids
            )
            
            logger.info(
                f"Added {len(documents)} documents to collection '{collection_name}'"
            )
            
        except Exception as e:
            logger.error(f"Failed to add documents: {e}", exc_info=True)
            raise
    
    def query(
        self,
        query_text: str,
        collection_name: str,
        n_results: int = 5
    ) -> Dict[str, Any]:
        """
        Query the vector store for similar documents
        
        Args:
            query_text: The search query
            collection_name: Name of the collection to search
            n_results: Number of results to return
        
        Returns:
            Dict with 'documents', 'metadatas', 'distances', 'ids'
        """
        try:
            collection = self.client.get_collection(name=collection_name)
            
            results = collection.query(
                query_texts=[query_text],
                n_results=n_results
            )
            
            # Flatten results (query_texts is a list, but we only have one)
            return {
                "documents": results["documents"][0] if results["documents"] else [],
                "metadatas": results["metadatas"][0] if results["metadatas"] else [],
                "distances": results["distances"][0] if results["distances"] else [],
                "ids": results["ids"][0] if results["ids"] else []
            }
            
        except Exception as e:
            logger.error(f"Failed to query collection '{collection_name}': {e}", exc_info=True)
            # Return empty results instead of raising
            return {
                "documents": [],
                "metadatas": [],
                "distances": [],
                "ids": []
            }
    
    def delete_collection(self, collection_name: str) -> None:
        """Delete a collection"""
        try:
            self.client.delete_collection(name=collection_name)
            logger.info(f"Deleted collection '{collection_name}'")
        except Exception as e:
            logger.warning(f"Failed to delete collection '{collection_name}': {e}")
    
    def list_collections(self) -> List[str]:
        """List all collection names"""
        try:
            collections = self.client.list_collections()
            return [col.name for col in collections]
        except Exception as e:
            logger.error(f"Failed to list collections: {e}", exc_info=True)
            return []
