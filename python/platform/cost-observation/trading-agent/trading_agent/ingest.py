"""Ingest documents into the Voyage AI + ChromaDB RAG knowledge base.

Usage
-----
    # Ingest all .txt / .md / .pdf files from a directory:
    python -m trading_agent.ingest path/to/docs/

    # Ingest a single file:
    python -m trading_agent.ingest path/to/report.txt

    # Custom chunk size / overlap:
    python -m trading_agent.ingest path/to/docs/ --chunk-size 800 --chunk-overlap 150
"""

from __future__ import annotations

import argparse
import hashlib
import logging
import os
import pathlib
import sys
import textwrap
import uuid

import chromadb
import voyageai

# Re-use the same constants as the retrieval tool
from trading_agent.rag import (
    CHROMA_COLLECTION,
    CHROMA_PERSIST_DIR,
    VOYAGE_MODEL,
)

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s  %(levelname)-8s  %(message)s"
)

# Supported file extensions
SUPPORTED_EXTENSIONS = {".txt", ".md", ".csv", ".json", ".log", ".pdf"}


# ---------------------------------------------------------------------------
# Text chunking (paragraph-aware)
# ---------------------------------------------------------------------------
def chunk_text(
    text: str,
    chunk_size: int = 512,
    chunk_overlap: int = 100,
) -> list[str]:
    """Split text into overlapping chunks, trying to break on paragraph boundaries.

    First splits on double-newlines (paragraphs), then merges small paragraphs
    together up to chunk_size.  Falls back to character-level splitting for any
    paragraph that exceeds chunk_size on its own.

    Args:
        text: The full document text.
        chunk_size: Maximum characters per chunk.
        chunk_overlap: Number of overlapping characters between consecutive chunks.

    Returns:
        A list of text chunks.
    """
    if len(text) <= chunk_size:
        return [text]

    # Split into paragraphs first
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    chunks: list[str] = []
    current_chunk = ""

    for para in paragraphs:
        # If a single paragraph exceeds chunk_size, split it by characters
        if len(para) > chunk_size:
            # Flush current buffer
            if current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = ""
            # Character-level split for oversized paragraphs
            start = 0
            while start < len(para):
                end = start + chunk_size
                chunks.append(para[start:end].strip())
                start += chunk_size - chunk_overlap
        elif len(current_chunk) + len(para) + 2 <= chunk_size:
            current_chunk = (current_chunk + "\n\n" + para).strip()
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            # Keep the tail of the previous chunk as overlap context
            if current_chunk and chunk_overlap > 0:
                overlap_text = current_chunk[-chunk_overlap:]
                current_chunk = overlap_text + "\n\n" + para
            else:
                current_chunk = para

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return [c for c in chunks if c]


# ---------------------------------------------------------------------------
# File reading (with PDF support)
# ---------------------------------------------------------------------------
def read_pdf(path: pathlib.Path) -> str:
    """Extract text from a PDF file using PyMuPDF (fitz)."""
    try:
        import fitz  # PyMuPDF
    except ImportError:
        logger.error(
            "PyMuPDF is required for PDF ingestion. "
            "Install it:  pip install PyMuPDF"
        )
        return ""

    try:
        doc = fitz.open(str(path))
        pages: list[str] = []
        for page in doc:
            text = page.get_text("text")
            if text.strip():
                pages.append(text)
        doc.close()
        return "\n\n".join(pages)
    except Exception as exc:
        logger.error("Failed to read PDF %s: %s", path, exc)
        return ""


def read_file(path: pathlib.Path) -> str:
    """Read a single file and return its text content."""
    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        logger.warning("Skipping unsupported file type: %s", path)
        return ""

    if suffix == ".pdf":
        return read_pdf(path)

    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        logger.error("Failed to read %s: %s", path, exc)
        return ""


def collect_files(root: pathlib.Path) -> list[pathlib.Path]:
    """Recursively collect all supported files under *root*."""
    if root.is_file():
        return [root] if root.suffix.lower() in SUPPORTED_EXTENSIONS else []

    files: list[pathlib.Path] = []
    for ext in SUPPORTED_EXTENSIONS:
        files.extend(root.rglob(f"*{ext}"))
    return sorted(set(files))


# ---------------------------------------------------------------------------
# Ingestion
# ---------------------------------------------------------------------------
def ingest(
    source: pathlib.Path,
    chunk_size: int = 512,
    chunk_overlap: int = 100,
    batch_size: int = 64,
) -> None:
    """Ingest documents from *source* into ChromaDB with Voyage embeddings.

    Args:
        source: Path to a file or directory of files.
        chunk_size: Characters per chunk.
        chunk_overlap: Overlap between chunks.
        batch_size: Number of chunks to embed per Voyage API call.
    """
    api_key = os.getenv("VOYAGE_API_KEY")
    if not api_key:
        logger.error("VOYAGE_API_KEY is not set. Add it to your .env file.")
        sys.exit(1)

    vo = voyageai.Client(api_key=api_key)

    # ChromaDB persistent client
    chroma = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
    collection = chroma.get_or_create_collection(
        name=CHROMA_COLLECTION,
        metadata={"hnsw:space": "cosine"},
    )

    files = collect_files(source)
    if not files:
        logger.error("No supported files found in %s", source)
        logger.info("Supported extensions: %s", ", ".join(sorted(SUPPORTED_EXTENSIONS)))
        sys.exit(1)

    logger.info("Found %d file(s) to ingest.", len(files))

    all_chunks: list[str] = []
    all_ids: list[str] = []
    all_metas: list[dict] = []

    for fpath in files:
        text = read_file(fpath)
        if not text.strip():
            continue

        chunks = chunk_text(text, chunk_size, chunk_overlap)
        logger.info("  %s  →  %d chunk(s)", fpath.name, len(chunks))

        for idx, chunk in enumerate(chunks):
            # Deterministic ID so re-ingesting the same file doesn't duplicate
            content_hash = hashlib.sha256(chunk.encode()).hexdigest()[:16]
            doc_id = f"{fpath.stem}_{idx}_{content_hash}"

            all_chunks.append(chunk)
            all_ids.append(doc_id)
            all_metas.append(
                {
                    "source": str(fpath.relative_to(source) if source.is_dir() else fpath.name),
                    "category": fpath.parent.name if fpath.parent != source else "general",
                    "chunk_index": idx,
                    "total_chunks": len(chunks),
                }
            )

    if not all_chunks:
        logger.error("All files were empty or unreadable.")
        sys.exit(1)

    logger.info("Embedding %d total chunk(s) with Voyage AI (%s)…", len(all_chunks), VOYAGE_MODEL)

    # Embed and upsert in batches
    for i in range(0, len(all_chunks), batch_size):
        batch_texts = all_chunks[i : i + batch_size]
        batch_ids = all_ids[i : i + batch_size]
        batch_metas = all_metas[i : i + batch_size]

        embed_result = vo.embed(
            texts=batch_texts,
            model=VOYAGE_MODEL,
            input_type="document",
        )

        collection.upsert(
            ids=batch_ids,
            embeddings=embed_result.embeddings,
            documents=batch_texts,
            metadatas=batch_metas,
        )
        logger.info(
            "  Upserted batch %d–%d / %d",
            i + 1,
            min(i + batch_size, len(all_chunks)),
            len(all_chunks),
        )

    logger.info(
        "✅ Done!  Collection '%s' now has %d document(s).",
        CHROMA_COLLECTION,
        collection.count(),
    )
    logger.info("   ChromaDB path: %s", CHROMA_PERSIST_DIR)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingest documents into the Voyage AI + ChromaDB RAG knowledge base.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Examples:
              python -m trading_agent.ingest ./docs/
              python -m trading_agent.ingest ./reports/q2_earnings.txt
              python -m trading_agent.ingest ./research/ --chunk-size 800 --chunk-overlap 150
        """),
    )
    parser.add_argument(
        "source",
        type=pathlib.Path,
        help="Path to a file or directory of documents to ingest.",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=512,
        help="Max characters per chunk (default: 512).",
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=100,
        help="Character overlap between chunks (default: 100).",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=64,
        help="Chunks per Voyage API embedding call (default: 64).",
    )
    args = parser.parse_args()

    if not args.source.exists():
        logger.error("Source path does not exist: %s", args.source)
        sys.exit(1)

    ingest(
        source=args.source,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
        batch_size=args.batch_size,
    )


if __name__ == "__main__":
    main()
