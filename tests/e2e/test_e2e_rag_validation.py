"""
E2E RAG Validation Test

This test validates the RAG pipeline with a REAL PDF file.
It does NOT test the full API, but PROVES that:
1. PDF text extraction works
2. ChromaDB vectorization works
3. Context retrieval returns real chunks from the PDF

This is a minimal test that focuses ONLY on the RAG components.
"""
import sys
from pathlib import Path
import tempfile
import shutil
import uuid

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "Backend" / "src_v3"))

# Now import
from infrastructure.ai.rag.chroma_store import ChromaVectorStore
from infrastructure.ai.rag.document_processor import DocumentProcessor


def test_find_real_pdf():
    """Test 1: Verify we can find the real PDF file"""
    pdf_files = list(project_root.glob("*.pdf"))
    
    assert len(pdf_files) > 0, "❌ No PDF file found in project root"
    
    pdf_path = pdf_files[0]
    print(f"✅ Found PDF: {pdf_path.name}")
    print(f"   Size: {pdf_path.stat().st_size:,} bytes")
    
    return str(pdf_path)


def test_extract_text_from_pdf():
    """Test 2: Extract text from the real PDF"""
    pdf_path = test_find_real_pdf()
    
    processor = DocumentProcessor(chunk_size=1000, chunk_overlap=200)
    documents = processor.process_pdf(pdf_path)
    
    assert len(documents) > 0, "❌ No documents extracted from PDF"
    
    print(f"✅ Extracted {len(documents)} chunks")
    print(f"   First chunk preview: {documents[0]['content'][:150]}...")
    print(f"   Metadata: {documents[0]['metadata']}")
    
    return documents


def test_store_in_chromadb():
    """Test 3: Store vectors in ChromaDB"""
    documents = test_extract_text_from_pdf()
    
    # Create temp directory for ChromaDB
    temp_dir = tempfile.mkdtemp(prefix="chroma_rag_test_")
    
    try:
        store = ChromaVectorStore(persist_directory=temp_dir)
        collection_name = f"test_rag_{uuid.uuid4().hex[:8]}"
        
        store.add_documents(documents, collection_name)
        
        # Verify collection exists
        collections = store.list_collections()
        assert collection_name in collections, "❌ Collection not created"
        
        print(f"✅ Stored {len(documents)} vectors in collection: {collection_name}")
        
        return store, collection_name, documents
        
    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_query_and_verify_context():
    """Test 4: Query ChromaDB and verify we get REAL context"""
    temp_dir = tempfile.mkdtemp(prefix="chroma_rag_test_")
    
    try:
        # Re-run ingestion
        pdf_path = test_find_real_pdf()
        processor = DocumentProcessor(chunk_size=1000, chunk_overlap=200)
        documents = processor.process_pdf(pdf_path)
        
        store = ChromaVectorStore(persist_directory=temp_dir)
        collection_name = f"test_query_{uuid.uuid4().hex[:8]}"
        store.add_documents(documents, collection_name)
        
        # Query with relevant terms
        query_text = "Python programming estructuras secuenciales variables"
        results = store.query(query_text, collection_name, n_results=3)
        
        assert "documents" in results, "❌ No documents in results"
        assert len(results["documents"]) > 0, "❌ No results returned"
        
        retrieved_chunks = results["documents"]
        
        print(f"✅ Query returned {len(retrieved_chunks)} chunks")
        print(f"   Query: {query_text}")
        print(f"\n📄 Retrieved Context (Top 3 chunks):")
        print("="*70)
        
        for i, chunk in enumerate(retrieved_chunks[:3], 1):
            print(f"\nChunk {i} ({len(chunk)} chars):")
            print(f"{chunk[:300]}...")
            print("-"*70)
        
        # CRITICAL ASSERTION: Verify chunks contain actual text
        total_length = sum(len(chunk) for chunk in retrieved_chunks)
        assert total_length > 500, f"❌ Retrieved context too short: {total_length} chars"
        
        # Verify chunks are not empty
        assert all(len(chunk) > 0 for chunk in retrieved_chunks), "❌ Empty chunks found"
        
        print(f"\n✅ CRITICAL VALIDATION PASSED")
        print(f"   Total context retrieved: {total_length} characters")
        print(f"   All chunks contain real text from PDF")
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_rag_pipeline_end_to_end():
    """Test 5: Complete RAG pipeline E2E"""
    print("\n" + "="*70)
    print("🚀 STARTING RAG PIPELINE E2E TEST")
    print("="*70)
    
    # Step 1: Find PDF
    print("\n[1/4] Finding real PDF...")
    pdf_path = test_find_real_pdf()
    
    # Step 2: Extract text
    print("\n[2/4] Extracting text from PDF...")
    processor = DocumentProcessor(chunk_size=1000, chunk_overlap=200)
    documents = processor.process_pdf(pdf_path)
    print(f"     Extracted {len(documents)} chunks")
    
    # Step 3: Store in ChromaDB
    print("\n[3/4] Storing vectors in ChromaDB...")
    temp_dir = tempfile.mkdtemp(prefix="chroma_rag_test_")
    
    try:
        store = ChromaVectorStore(persist_directory=temp_dir)
        collection_name = f"e2e_test_{uuid.uuid4().hex[:8]}"
        store.add_documents(documents, collection_name)
        print(f"     Stored {len(documents)} vectors")
        
        # Step 4: Query and verify
        print("\n[4/4] Querying ChromaDB...")
        query_text = "Python estructuras secuenciales"
        results = store.query(query_text, collection_name, n_results=5)
        
        retrieved = results["documents"]
        print(f"     Retrieved {len(retrieved)} chunks")
        
        # Assertions
        assert len(retrieved) > 0, "❌ No results retrieved"
        total_chars = sum(len(chunk) for chunk in retrieved)
        assert total_chars > 1000, f"❌ Context too short: {total_chars} chars"
        
        print("\n" + "="*70)
        print("✅ RAG PIPELINE E2E TEST PASSED")
        print("="*70)
        print(f"   PDF: {Path(pdf_path).name}")
        print(f"   Chunks extracted: {len(documents)}")
        print(f"   Chunks stored in ChromaDB: {len(documents)}")
        print(f"   Chunks retrieved: {len(retrieved)}")
        print(f"   Total context length: {total_chars} characters")
        print("="*70)
        
        print("\n📊 Sample Retrieved Context:")
        print("-"*70)
        print(retrieved[0][:500])
        print("...")
        print("-"*70)
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    test_rag_pipeline_end_to_end()
