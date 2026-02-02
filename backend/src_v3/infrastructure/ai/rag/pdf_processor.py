"""
PDF Processor for RAG - Extract and store PDF content in vector database
"""
from pathlib import Path
from typing import List, Dict, Optional
import hashlib
import re


class PDFProcessor:
    """Process PDF files and extract content for RAG"""
    
    def __init__(self, chroma_service):
        """Initialize with ChromaDB service"""
        self.chroma_service = chroma_service
    
    def extract_text_from_pdf(self, pdf_path: Path) -> str:
        """Extract text from PDF file
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Extracted text content
        """
        try:
            # Try PyPDF2 first (most common)
            import PyPDF2
            
            text_content = []
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    text = page.extract_text()
                    if text.strip():
                        text_content.append(f"[Página {page_num}]\n{text}")
            
            return "\n\n".join(text_content)
            
        except ImportError:
            # Fallback to pdfplumber if available
            try:
                import pdfplumber
                
                text_content = []
                with pdfplumber.open(pdf_path) as pdf:
                    for page_num, page in enumerate(pdf.pages, 1):
                        text = page.extract_text()
                        if text:
                            text_content.append(f"[Página {page_num}]\n{text}")
                
                return "\n\n".join(text_content)
                
            except ImportError:
                raise ImportError(
                    "No PDF library available. Install PyPDF2 or pdfplumber: "
                    "pip install PyPDF2 pdfplumber"
                )
    
    def chunk_text(
        self,
        text: str,
        chunk_size: int = 1000,
        overlap: int = 200
    ) -> List[str]:
        """Split text into overlapping chunks
        
        Args:
            text: Full text content
            chunk_size: Maximum size of each chunk
            overlap: Number of characters to overlap between chunks
            
        Returns:
            List of text chunks
        """
        # Clean text
        text = re.sub(r'\s+', ' ', text).strip()
        
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence endings
                sentence_end = text.rfind('.', start, end)
                if sentence_end > start + chunk_size // 2:
                    end = sentence_end + 1
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Move start position with overlap
            start = end - overlap if end < len(text) else end
        
        return chunks
    
    def generate_chunk_id(self, activity_id: str, filename: str, chunk_idx: int) -> str:
        """Generate unique ID for a chunk"""
        content = f"{activity_id}_{filename}_{chunk_idx}"
        return hashlib.md5(content.encode()).hexdigest()
    
    async def process_and_store(
        self,
        pdf_path: Path,
        activity_id: str,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """Process PDF and store in vector database
        
        Args:
            pdf_path: Path to PDF file
            activity_id: Activity ID for metadata
            metadata: Additional metadata
            
        Returns:
            Processing results with statistics
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        # Extract text
        text = self.extract_text_from_pdf(pdf_path)
        
        if not text.strip():
            return {
                "success": False,
                "error": "No text content extracted from PDF",
                "chunks_stored": 0
            }
        
        # Split into chunks
        chunks = self.chunk_text(text)
        
        # Prepare metadata
        base_metadata = {
            "activity_id": activity_id,
            "filename": pdf_path.name,
            "language": "python",
            "type": "pedagogical_content",
            "source": "teacher_upload"
        }
        
        if metadata:
            base_metadata.update(metadata)
        
        # Prepare for storage
        documents = []
        metadatas = []
        ids = []
        
        for idx, chunk in enumerate(chunks):
            chunk_id = self.generate_chunk_id(activity_id, pdf_path.name, idx)
            chunk_metadata = base_metadata.copy()
            chunk_metadata["chunk_index"] = idx
            chunk_metadata["total_chunks"] = len(chunks)
            
            documents.append(chunk)
            metadatas.append(chunk_metadata)
            ids.append(chunk_id)
        
        # Store in ChromaDB
        try:
            self.chroma_service.add_documents(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            return {
                "success": True,
                "filename": pdf_path.name,
                "chunks_stored": len(chunks),
                "total_chars": len(text),
                "activity_id": activity_id
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error storing in vector database: {str(e)}",
                "chunks_stored": 0
            }
    
    def get_context_for_activity(
        self,
        activity_id: str,
        query: str,
        n_results: int = 3
    ) -> str:
        """Retrieve relevant context for an activity
        
        Args:
            activity_id: Activity ID to filter by
            query: Search query
            n_results: Number of results to return
            
        Returns:
            Combined context text
        """
        contexts = self.chroma_service.search(
            query=query,
            n_results=n_results,
            filters={"activity_id": activity_id}
        )
        
        if not contexts:
            return ""
        
        # Combine contexts with source information
        combined = []
        for ctx in contexts:
            metadata = ctx.get('metadata', {})
            content = ctx.get('content', '')
            filename = metadata.get('filename', 'unknown')
            chunk_idx = metadata.get('chunk_index', 0)
            
            combined.append(
                f"[Fuente: {filename} - Fragmento {chunk_idx + 1}]\n{content}"
            )
        
        return "\n\n---\n\n".join(combined)
