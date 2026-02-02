"""Quick test to verify new PDF is readable"""
import sys
from pathlib import Path

# Add Backend to path
backend_path = Path(__file__).parent.parent / "Backend"
sys.path.insert(0, str(backend_path))

from src_v3.infrastructure.ai.rag.document_processor import DocumentProcessor

# Find PDF
project_root = Path(__file__).parent.parent
pdf_path = project_root / "Algoritmia y Programación - U1 - 4.pdf"

print(f"Testing PDF: {pdf_path}")
print(f"PDF exists: {pdf_path.exists()}")

# Try to extract text
processor = DocumentProcessor()
documents = processor.process_pdf(str(pdf_path))

print(f"\n✅ SUCCESS! Extracted {len(documents)} chunks")
if documents:
    print(f"\nFirst chunk preview:")
    print(f"Content length: {len(documents[0]['content'])} chars")
    print(f"Content: {documents[0]['content'][:200]}...")
    print(f"Metadata: {documents[0]['metadata']}")
else:
    print("\n❌ FAILED - No text extracted")
