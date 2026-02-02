"""
Simplified E2E Test - Validates Real RAG Pipeline
Run directly: python Test/test_e2e_validation.py
"""
import sys
from pathlib import Path

# Add Backend to path
backend_path = Path(__file__).parent.parent / "Backend"
sys.path.insert(0, str(backend_path))

print("=" * 70)
print("E2E VALIDATION - REAL RAG PIPELINE TEST")
print("=" * 70)

# Test 1: Find PDF
print("\n[1/5] Locating PDF file...")
project_root = Path(__file__).parent.parent
pdf_files = list(project_root.glob("*.pdf"))
assert len(pdf_files) > 0, "No PDF found in project root"
pdf_path = pdf_files[0]
print(f"✅ Found: {pdf_path.name} ({pdf_path.stat().st_size:,} bytes)")

# Test 2: Extract text from PDF
print("\n[2/5] Extracting text from PDF...")
from src_v3.infrastructure.ai.rag.document_processor import DocumentProcessor

processor = DocumentProcessor(chunk_size=1000, chunk_overlap=200)
documents = processor.process_pdf(str(pdf_path))

assert len(documents) > 0, f"No text extracted from {pdf_path.name}"
print(f"✅ Extracted {len(documents)} chunks")
print(f"   First chunk: {documents[0]['content'][:150]}...")
print(f"   Metadata: {documents[0]['metadata']}")

# Test 3: Store in ChromaDB
print("\n[3/5] Storing vectors in ChromaDB...")
import tempfile
import uuid

temp_dir = tempfile.mkdtemp(prefix="chroma_e2e_")
from src_v3.infrastructure.ai.rag.chroma_store import ChromaVectorStore

vector_store = ChromaVectorStore(persist_directory=temp_dir)
collection_name = f"test_e2e_{uuid.uuid4().hex[:8]}"

vector_store.add_documents(
    documents=documents,
    collection_name=collection_name
)

# Verify collection exists
collections = vector_store.list_collections()
assert collection_name in collections, "Collection not created"
print(f"✅ Stored in collection: {collection_name}")
print(f"   Total collections: {len(collections)}")

# Test 4: Query vectors (Real RAG)
print("\n[4/5] Querying vectors (Real RAG context retrieval)...")
query = "estructuras secuenciales Python programación"
results = vector_store.query(
    query_text=query,
    collection_name=collection_name,
    n_results=3
)

assert len(results["documents"]) > 0, "No results from query"
assert all(len(doc) > 0 for doc in results["documents"]), "Empty documents in results"

print(f"✅ Retrieved {len(results['documents'])} relevant chunks")
print(f"   Query: '{query}'")
print(f"   Top result: {results['documents'][0][:200]}...")
print(f"   Similarity scores: {results['distances']}")

# Test 5: Verify context contains actual PDF text
print("\n[5/5] Validating RAG context authenticity...")

# Extract some unique text from the first document
unique_text_from_pdf = documents[0]['content'][:50].strip()
retrieved_text = ' '.join(results['documents'])

# Check if any retrieved chunk contains actual PDF content
contains_real_content = any(
    doc_chunk in ' '.join([d['content'] for d in documents])
    for doc_chunk in results['documents']
)

assert contains_real_content, "Retrieved context does not match PDF content!"
print(f"✅ CRITICAL VALIDATION PASSED")
print(f"   Retrieved context contains REAL text from PDF")
print(f"   Sample match: '{results['documents'][0][:100]}...'")

# Cleanup
import shutil
shutil.rmtree(temp_dir, ignore_errors=True)

print("\n" + "=" * 70)
print("🎉 ALL E2E TESTS PASSED!")
print("=" * 70)
print("\n✅ PDF Processing: Working")
print("✅ Text Extraction: Working")
print("✅ ChromaDB Storage: Working")
print("✅ Vector Retrieval: Working")
print("✅ RAG Context: AUTHENTIC (contains real PDF text)")
print("\n" + "=" * 70)
print("READY FOR MISTRAL LLM INTEGRATION")
print("=" * 70)
