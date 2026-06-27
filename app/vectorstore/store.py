"""
store.py — ChromaDB Vector Store Setup, Ingestion, and Retrieval
================================================================
WHAT THIS FILE DOES:
    Three responsibilities:
    1. SETUP    — connects to (or creates) a persistent ChromaDB collection
    2. INGEST   — loads .txt documents, splits them into chunks, embeds
                  each chunk, and stores everything in ChromaDB
    3. RETRIEVE — takes a natural language query and returns the most
                  semantically relevant chunks from ChromaDB

KEY CONCEPTS IN THIS FILE:

    RecursiveCharacterTextSplitter:
        Splits text into chunks. "Recursive" means it tries to split
        on paragraph breaks first (\\n\\n), then sentences (\\n),
        then words ( ), then characters — always trying to keep splits
        at natural language boundaries.

        chunk_size=800   → each chunk is at most 800 characters
        chunk_overlap=100 → neighbouring chunks share 100 characters
                           This prevents important context being lost
                           at a chunk boundary.

    Chroma (LangChain wrapper):
        A LangChain class that wraps the raw ChromaDB library.
        It stores documents with their embeddings and handles the
        similarity search internally. We use the LangChain wrapper
        (not raw ChromaDB) because it integrates seamlessly with
        LangChain's retriever interface (used in the RAG engine later).

    persist_directory:
        ChromaDB saves its data to disk here. When you restart the app,
        it loads from this folder — you don't need to re-embed every time.

HOW TO RUN INGESTION:
    From the project root with venv activated:
        python -m app.vectorstore.store
    This loads all .txt files from data/documents/ and embeds them.
"""

import os
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from langchain.schema import Document
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from loguru import logger

from app.vectorstore.embedder import get_embedding_model

load_dotenv(override=True)

# ── Configuration ─────────────────────────────────────────────────────────────
# Where ChromaDB will persist its data files on disk
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "data/chroma")

# The collection name inside ChromaDB — like a "table name" in SQL
CHROMA_COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "hr_docs")

# Where our source documents live
DOCUMENTS_DIR = "data/documents"

# Chunking parameters — tune these based on your document length
CHUNK_SIZE = 800      # Max characters per chunk
CHUNK_OVERLAP = 100   # Characters shared between adjacent chunks


# ═══════════════════════════════════════════════════════════════════
# PART 1: Setup — get or create the ChromaDB collection
# ═══════════════════════════════════════════════════════════════════
def get_vectorstore() -> Chroma:
    """
    Returns a LangChain Chroma vectorstore connected to our persistent
    ChromaDB collection. Creates the collection if it doesn't exist.

    This is a lightweight operation — it just opens the connection.
    It does NOT re-embed documents. If the persist_directory already
    has data, it loads that data.

    Returns:
        Chroma: a LangChain vectorstore ready for similarity search.
    """
    # Ensure the persist directory exists before ChromaDB tries to use it
    Path(CHROMA_PERSIST_DIR).mkdir(parents=True, exist_ok=True)

    embedding_model = get_embedding_model()

    # Chroma() opens an existing collection or creates a new empty one.
    # persist_directory tells ChromaDB where to read/write its files.
    vectorstore = Chroma(
        collection_name=CHROMA_COLLECTION_NAME,
        embedding_function=embedding_model,
        persist_directory=CHROMA_PERSIST_DIR,
    )

    return vectorstore


# ═══════════════════════════════════════════════════════════════════
# PART 2: Load — read .txt files and convert to LangChain Documents
# ═══════════════════════════════════════════════════════════════════
def load_documents(docs_dir: str = DOCUMENTS_DIR) -> List[Document]:
    """
    Reads all .txt files from the documents directory.

    A LangChain Document is a simple object with two fields:
        - page_content : the raw text
        - metadata     : a dict of extra info (filename, source, etc.)

    We store the filename in metadata so that when the RAG engine
    returns a chunk, we know WHICH document it came from.
    This is important for citations and debugging.

    Args:
        docs_dir: path to the folder containing .txt files

    Returns:
        List[Document]: one Document per file (not yet chunked)
    """
    docs_path = Path(docs_dir)
    if not docs_path.exists():
        raise FileNotFoundError(f"Documents directory not found: {docs_dir}")

    documents = []
    txt_files = list(docs_path.glob("*.txt"))

    if not txt_files:
        raise ValueError(f"No .txt files found in {docs_dir}")

    for file_path in txt_files:
        text = file_path.read_text(encoding="utf-8")
        doc = Document(
            page_content=text,
            metadata={
                "source": file_path.name,       # e.g. "hr_leave_policy.txt"
                "file_path": str(file_path),
            },
        )
        documents.append(doc)
        logger.info(f"Loaded: {file_path.name} ({len(text):,} characters)")

    return documents


# ═══════════════════════════════════════════════════════════════════
# PART 3: Chunk — split documents into small overlapping pieces
# ═══════════════════════════════════════════════════════════════════
def chunk_documents(documents: List[Document]) -> List[Document]:
    """
    Splits each Document into smaller chunks using
    RecursiveCharacterTextSplitter.

    WHY RECURSIVE?
        It tries splitting at paragraph breaks (\\n\\n) first.
        If that produces chunks that are still too large, it tries
        sentence breaks (\\n), then words, then characters.
        This ensures chunks always split at natural boundaries.

    The metadata from the parent document is COPIED to every chunk.
    So if hr_leave_policy.txt is split into 6 chunks, each chunk
    still knows its source is "hr_leave_policy.txt".

    Args:
        documents: list of full-document LangChain Documents

    Returns:
        List[Document]: many smaller chunk Documents
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        # These separators are tried in order from most to least preferred
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks = splitter.split_documents(documents)
    logger.info(
        f"Split {len(documents)} document(s) into {len(chunks)} chunks "
        f"(chunk_size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})"
    )
    return chunks


# ═══════════════════════════════════════════════════════════════════
# PART 4: Ingest — embed chunks and store in ChromaDB
# ═══════════════════════════════════════════════════════════════════
def ingest_documents(docs_dir: str = DOCUMENTS_DIR, force: bool = False) -> int:
    """
    Full ingestion pipeline: load → chunk → embed → store.

    This function is idempotent by default — if documents are already
    in ChromaDB, it skips the ingestion to avoid duplicates and
    unnecessary API calls. Use force=True to re-ingest everything.

    Args:
        docs_dir: path to folder containing .txt files
        force: if True, clears the collection and re-ingests

    Returns:
        int: number of chunks stored in ChromaDB
    """
    logger.info("Starting document ingestion pipeline...")

    vectorstore = get_vectorstore()

    # Check if documents already exist in the collection
    existing_count = vectorstore._collection.count()
    if existing_count > 0 and not force:
        logger.info(
            f"ChromaDB already contains {existing_count} chunks — skipping ingestion. "
            f"Use force=True to re-ingest."
        )
        return existing_count

    if force and existing_count > 0:
        logger.warning("force=True: clearing existing collection before re-ingesting.")
        vectorstore._collection.delete(
            where={"source": {"$ne": ""}}  # Delete all documents
        )

    # Step 1: Load raw documents from disk
    documents = load_documents(docs_dir)

    # Step 2: Split into chunks
    chunks = chunk_documents(documents)

    # Step 3: Embed and store (this is the API call to OpenAI)
    # Chroma.add_documents() does three things internally:
    #   a) Calls get_embedding_model().embed_documents(texts) for each chunk
    #   b) Assigns a unique ID to each chunk
    #   c) Persists everything to disk in CHROMA_PERSIST_DIR
    logger.info(f"Embedding {len(chunks)} chunks — this will call the OpenAI API...")
    vectorstore.add_documents(chunks)
    logger.success(f"Ingestion complete! {len(chunks)} chunks stored in ChromaDB.")
    logger.info(f"ChromaDB data saved to: {CHROMA_PERSIST_DIR}")

    return len(chunks)


# ═══════════════════════════════════════════════════════════════════
# PART 5: Retrieve — similarity search
# ═══════════════════════════════════════════════════════════════════
def retrieve(query: str, k: int = None) -> List[Document]:
    """
    Finds the top-k most relevant document chunks for a given query.

    HOW IT WORKS:
        1. Embeds the query text into a vector using OpenAI
        2. Computes cosine similarity between the query vector and
           every stored chunk vector in ChromaDB
        3. Returns the k chunks with the highest similarity scores

    The returned Documents have:
        - .page_content : the actual text of the matching chunk
        - .metadata     : {"source": "hr_leave_policy.txt", ...}

    Args:
        query: the natural language question to search for
        k: how many chunks to return (reads TOP_K_RETRIEVAL from env)

    Returns:
        List[Document]: the most relevant chunks, ranked by similarity
    """
    if k is None:
        k = int(os.getenv("TOP_K_RETRIEVAL", "5"))

    vectorstore = get_vectorstore()

    # similarity_search embeds the query and returns the top-k matches
    results = vectorstore.similarity_search(query, k=k)

    logger.debug(f"Retrieved {len(results)} chunks for query: '{query[:60]}...'")
    return results


def retrieve_with_scores(query: str, k: int = None) -> List[tuple]:
    """
    Same as retrieve() but also returns the similarity score for each chunk.
    Useful for debugging — you can see HOW similar each result is.

    Returns:
        List[tuple]: [(Document, score), ...] sorted by score descending
                     Score is a distance metric (lower = more similar in some backends)
    """
    if k is None:
        k = int(os.getenv("TOP_K_RETRIEVAL", "5"))

    vectorstore = get_vectorstore()
    results = vectorstore.similarity_search_with_score(query, k=k)
    return results


# ═══════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT — run ingestion directly
# ═══════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    ingest_documents()
