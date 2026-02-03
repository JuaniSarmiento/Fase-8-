"""
Debug PDF extraction
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "Backend" / "src_v3"))

# Find PDF
pdf_files = list(project_root.glob("*.pdf"))
if not pdf_files:
    print("❌ No PDF found")
    sys.exit(1)

pdf_path = pdf_files[0]
print(f"📄 Testing PDF: {pdf_path.name}")
print(f"   Size: {pdf_path.stat().st_size:,} bytes\n")

# Test with pypdf directly
print("="*70)
print("TEST 1: Direct pypdf extraction")
print("="*70)

try:
    import pypdf
    
    with open(pdf_path, 'rb') as file:
        reader = pypdf.PdfReader(file)
        
        print(f"Total pages: {len(reader.pages)}")
        
        for page_num in range(min(3, len(reader.pages))):  # First 3 pages
            page = reader.pages[page_num]
            text = page.extract_text()
            
            print(f"\n--- Page {page_num + 1} ---")
            print(f"Length: {len(text)} chars")
            print(f"Preview: {text[:200]}...")
            
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

# Test with DocumentProcessor
print("\n" + "="*70)
print("TEST 2: DocumentProcessor")
print("="*70)

try:
    from infrastructure.ai.rag.document_processor import DocumentProcessor
    
    processor = DocumentProcessor(chunk_size=1000, chunk_overlap=200)
    documents = processor.process_pdf(str(pdf_path))
    
    print(f"✅ Extracted {len(documents)} chunks")
    
    if documents:
        print(f"\nFirst chunk:")
        print(f"  Content length: {len(documents[0]['content'])}")
        print(f"  Metadata: {documents[0]['metadata']}")
        print(f"  Preview: {documents[0]['content'][:200]}...")
    else:
        print("❌ No chunks extracted")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
