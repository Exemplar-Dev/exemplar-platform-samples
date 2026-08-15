"""RAG retrieval tool — Voyage AI embeddings + ChromaDB vector store.

Exposes `search_knowledge_base` as a plain function that Google ADK
auto-wraps into a FunctionTool.  The agent can call it whenever the user
asks questions that benefit from internal documents / notes / research.
"""

import logging
import os
import pathlib

import chromadb
import voyageai

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths & constants
# ---------------------------------------------------------------------------
_PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
CHROMA_PERSIST_DIR = str(_PROJECT_ROOT / "rag_data" / "chroma_db")
CHROMA_COLLECTION = os.getenv("RAG_COLLECTION", "trading_knowledge")
VOYAGE_MODEL = os.getenv("VOYAGE_EMBED_MODEL", "voyage-3")

# ---------------------------------------------------------------------------
# Lazy singletons (created on first call so import-time never crashes)
# ---------------------------------------------------------------------------
_vo_client: voyageai.Client | None = None
_chroma_collection: chromadb.Collection | None = None


def _get_voyage_client() -> voyageai.Client:
    global _vo_client
    if _vo_client is None:
        api_key = os.getenv("VOYAGE_API_KEY")
        if not api_key:
            raise RuntimeError(
                "VOYAGE_API_KEY is not set.  Add it to your .env file."
            )
        _vo_client = voyageai.Client(api_key=api_key)
    return _vo_client


def _get_chroma_collection() -> chromadb.Collection:
    global _chroma_collection
    if _chroma_collection is None:
        client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
        _chroma_collection = client.get_or_create_collection(
            name=CHROMA_COLLECTION,
            metadata={"hnsw:space": "cosine"},
        )
    return _chroma_collection


# ---------------------------------------------------------------------------
# ADK tool function
# ---------------------------------------------------------------------------
def search_knowledge_base(query: str, top_k: int = 5) -> str:
    """Search the internal knowledge base for documents relevant to a query.

    Use this tool when the user asks about internal research, trading notes,
    strategy documents, financial reports, or any previously ingested
    reference material that is NOT available via live TradingView data.

    Args:
        query: The search question or topic to look up.
        top_k: Maximum number of relevant snippets to return (default 5).

    Returns:
        A formatted string of the most relevant document snippets with their
        source metadata, or a message saying no relevant documents were found.
    """
    collection = _get_chroma_collection()

    # Check the collection has data
    if collection.count() == 0:
        return (
            "The knowledge base is empty.  No documents have been ingested yet. "
            "Run the ingestion script first:  python -m trading_agent.ingest --help"
        )

    # Embed the query with Voyage AI
    vo = _get_voyage_client()
    embed_result = vo.embed(
        texts=[query],
        model=VOYAGE_MODEL,
        input_type="query",
    )
    query_vector = embed_result.embeddings[0]

    # Query ChromaDB
    results = collection.query(
        query_embeddings=[query_vector],
        n_results=min(top_k, collection.count()),
        include=["documents", "metadatas", "distances"],
    )

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    if not documents:
        return "No relevant documents found in the knowledge base for this query."

    # Format results
    snippets: list[str] = []
    for i, (doc, meta, dist) in enumerate(
        zip(documents, metadatas, distances), start=1
    ):
        similarity = round(1.0 - dist, 4)  # cosine distance → similarity
        source = meta.get("source", "unknown") if meta else "unknown"
        snippets.append(
            f"--- Snippet {i} (similarity: {similarity}, source: {source}) ---\n{doc}"
        )

    header = f"Found {len(snippets)} relevant snippet(s) from the knowledge base:\n\n"
    return header + "\n\n".join(snippets)
