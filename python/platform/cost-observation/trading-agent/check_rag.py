"""Quick RAG test — search the knowledge base with a few queries."""
import os, pathlib, sys

# Load .env
p = pathlib.Path("D:/agents-testting/.env")
for line in p.read_text().splitlines():
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

from trading_agent.rag import search_knowledge_base

queries = [
    "What is the best risk management strategy?",
    "How do candlestick patterns work?",
    "Warren Buffett value investing principles",
    "EMA crossover trading strategy",
]

for q in queries:
    print(f"\n{'='*70}")
    print(f"QUERY: {q}")
    print(f"{'='*70}")
    result = search_knowledge_base(q, top_k=3)
    # Print just the first 400 chars of each snippet for brevity
    lines = result.split("--- Snippet")
    print(lines[0].strip())  # header
    for snippet in lines[1:]:
        # Show just first 200 chars of each
        truncated = snippet[:250].strip()
        print(f"--- Snippet{truncated}...")
    print()
