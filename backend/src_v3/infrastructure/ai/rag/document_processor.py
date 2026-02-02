"""
DocumentProcessor - Process PDFs and documents for RAG ingestion
"""
from pathlib import Path
from typing import List, Dict, Any
import hashlib
import logging
import re

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """
    Process documents (PDFs, text files) for vector store ingestion
    
    Extracts text, splits into chunks, and prepares metadata.
    """
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Initialize document processor
        
        Args:
            chunk_size: Size of each text chunk in characters
            chunk_overlap: Overlap between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def process_pdf(self, pdf_path: str) -> List[Dict[str, Any]]:
        """
        Process PDF file and extract chunks
        
        Args:
            pdf_path: Path to PDF file
        
        Returns:
            List of document dicts with 'content', 'metadata', 'id'
        """
        try:
            # Try using pypdf
            import pypdf
            
            pdf_file = Path(pdf_path)
            if not pdf_file.exists():
                raise FileNotFoundError(f"PDF not found: {pdf_path}")
            
            # Extract text from PDF
            text_content = []
            with open(pdf_file, 'rb') as file:
                reader = pypdf.PdfReader(file)
                
                for page_num, page in enumerate(reader.pages, start=1):
                    text = page.extract_text()
                    if text.strip():
                        text_content.append({
                            "text": text,
                            "page": page_num
                        })
            
            # Split into chunks
            documents = []
            doc_id_base = self._generate_doc_id(pdf_path)
            
            for page_data in text_content:
                page_text = page_data["text"]
                page_num = page_data["page"]
                
                # Split page into chunks
                chunks = self._split_text(page_text)
                
                for chunk_idx, chunk in enumerate(chunks):
                    if len(chunk.strip()) < 50:  # Skip very short chunks
                        continue
                    
                    documents.append({
                        "content": chunk,
                        "metadata": {
                            "source": str(pdf_file.name),
                            "page": page_num,
                            "chunk": chunk_idx,
                            "type": "pdf"
                        },
                        "id": f"{doc_id_base}_p{page_num}_c{chunk_idx}"
                    })
            
            logger.info(
                f"Processed PDF '{pdf_file.name}': {len(text_content)} pages, {len(documents)} chunks"
            )
            
            return documents
            
        except ImportError:
            logger.error("pypdf not installed. Install with: pip install pypdf")
            raise
        except Exception as e:
            logger.error(f"Failed to process PDF: {e}", exc_info=True)
            raise
    
    def process_text(self, text: str, source_name: str = "text") -> List[Dict[str, Any]]:
        """
        Process plain text and split into chunks
        
        Args:
            text: The text content
            source_name: Name of the source (for metadata)
        
        Returns:
            List of document dicts
        """
        chunks = self._split_text(text)
        doc_id_base = self._generate_doc_id(source_name)
        
        documents = []
        for chunk_idx, chunk in enumerate(chunks):
            if len(chunk.strip()) < 50:
                continue
            
            documents.append({
                "content": chunk,
                "metadata": {
                    "source": source_name,
                    "chunk": chunk_idx,
                    "type": "text"
                },
                "id": f"{doc_id_base}_c{chunk_idx}"
            })
        
        logger.info(f"Processed text: {len(documents)} chunks")
        return documents
    
    def _split_text(self, text: str) -> List[str]:
        """
        Split text into overlapping chunks
        
        Args:
            text: Text to split
        
        Returns:
            List of text chunks
        """
        # Clean text
        text = re.sub(r'\s+', ' ', text).strip()
        
        if len(text) <= self.chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence end within overlap zone
                sentence_end = text.rfind('.', end - 100, end)
                if sentence_end != -1:
                    end = sentence_end + 1
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Move start with overlap
            start = end - self.chunk_overlap
            if start <= 0:
                start = end
        
        return chunks
    
    def _generate_doc_id(self, source: str) -> str:
        """Generate unique document ID from source"""
        return hashlib.md5(source.encode()).hexdigest()[:12]
