"""
Phase 3 — RAG Knowledge Base Pipeline
Builds and queries a ChromaDB vector store from curated finance documents.
Project: Centsible AI
"""

import os
import chromadb

from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    Settings,
)
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

BASE_DIR          = os.path.dirname(os.path.dirname(__file__))
KNOWLEDGE_DIR     = os.path.join(BASE_DIR, 'knowledge_base')
CHROMA_STORE_DIR  = os.path.join(BASE_DIR, 'chroma_store')
COLLECTION_NAME   = 'centsible_finance_kb'

# Use a lightweight local embedding model — no API calls, runs on M4's Metal
EMBED_MODEL_NAME  = 'sentence-transformers/all-MiniLM-L6-v2'


def _get_embed_model():
    return HuggingFaceEmbedding(model_name=EMBED_MODEL_NAME)


def build_vector_store(force_rebuild: bool = False) -> VectorStoreIndex:
    """
    Reads all documents from knowledge_base/, chunks and embeds them,
    and persists to ChromaDB. If the store already exists, loads it.
    """
    Settings.embed_model = _get_embed_model()
    Settings.llm = None  # We handle LLM separately via Ollama

    chroma_client = chromadb.PersistentClient(path=CHROMA_STORE_DIR)

    existing_cols = [c.name for c in chroma_client.list_collections()]
    store_exists  = COLLECTION_NAME in existing_cols

    if store_exists and not force_rebuild:
        print(f"✅ Loading existing vector store from: {CHROMA_STORE_DIR}")
        collection    = chroma_client.get_collection(COLLECTION_NAME)
        vector_store  = ChromaVectorStore(chroma_collection=collection)
        storage_ctx   = StorageContext.from_defaults(vector_store=vector_store)
        index         = VectorStoreIndex.from_vector_store(vector_store, storage_context=storage_ctx)
        return index

    print(f"🔨 Building vector store from: {KNOWLEDGE_DIR}")

    if store_exists and force_rebuild:
        chroma_client.delete_collection(COLLECTION_NAME)
        print("   Deleted old collection for rebuild.")

    collection   = chroma_client.get_or_create_collection(COLLECTION_NAME)
    vector_store = ChromaVectorStore(chroma_collection=collection)
    storage_ctx  = StorageContext.from_defaults(vector_store=vector_store)

    documents = SimpleDirectoryReader(KNOWLEDGE_DIR).load_data()
    print(f"   Loaded {len(documents)} documents. Embedding now (first run takes ~30s)...")

    index = VectorStoreIndex.from_documents(
        documents,
        storage_context=storage_ctx,
        show_progress=True,
    )
    print(f"✅ Vector store built and saved → {CHROMA_STORE_DIR}")
    return index


def retrieve_context(user_question: str, index: VectorStoreIndex, top_k: int = 3) -> str:
    """
    Retrieves the top_k most relevant knowledge chunks for a given user question.
    Returns a single formatted string ready to inject into the LLM prompt.
    """
    retriever = index.as_retriever(similarity_top_k=top_k)
    nodes     = retriever.retrieve(user_question)

    if not nodes:
        return "No relevant knowledge found in the knowledge base."

    chunks = []
    for i, node in enumerate(nodes, 1):
        source = os.path.basename(node.metadata.get('file_name', f'doc_{i}'))
        chunks.append(f"[Source {i}: {source}]\n{node.text.strip()}")

    return "\n\n---\n\n".join(chunks)


if __name__ == '__main__':
    # Build (or load) the vector store
    index = build_vector_store(force_rebuild=False)

    # Test retrieval with sample financial questions
    test_queries = [
        "How much should I save each month?",
        "What is the 50/30/20 rule?",
        "How do I pay off credit card debt faster?",
        "I am a freelancer, how should I manage irregular income?",
        "How many months of expenses should my emergency fund cover?",
    ]

    print("\n" + "═" * 60)
    print("🔍 RAG Retrieval Test")
    print("═" * 60)

    for q in test_queries:
        print(f"\n❓ Question: {q}")
        context = retrieve_context(q, index)
        # Show only first 300 chars of retrieved context for readability
        preview = context[:300].replace('\n', ' ')
        print(f"   📄 Retrieved: {preview}...")
        print()
