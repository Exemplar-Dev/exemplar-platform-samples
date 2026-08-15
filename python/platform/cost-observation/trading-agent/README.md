# ADK Trading Agent

A [Google ADK](https://adk.dev/) agent that answers market and finance questions using **TradingView MCP** tools, **Voyage AI RAG** knowledge retrieval, and **Gemini 2.5 Pro** as the underlying LLM. Includes optional **Exemplar Cost Observability** integration to monitor LLM usage, tool calls, and orchestration costs.

## Architecture

```
User Query
   │
   ▼
ADK LlmAgent  ──model──▶  Gemini 2.5 Pro
   │
   ├──▶  tool: search_knowledge_base   (Voyage AI embeddings + ChromaDB)
   │
   └──▶  tool: McpToolset (stdio subprocess)
              └──▶  TradingView MCP Server
                       └──▶  TradingView / Yahoo Finance / Reddit / RSS
```

- **MCP transport:** stdio — ADK starts the MCP server as a child process automatically.
- **RAG:** Voyage AI embeddings with ChromaDB for persistent knowledge retrieval.
- **Observability (optional):** Exemplar Harness SDK captures composition, orchestration, and per-tool metrics. Fails open — the agent runs normally without it.

---

## Prerequisites

| Requirement       | Version    | Notes                                  |
| ----------------- | ---------- | -------------------------------------- |
| Python            | ≥ 3.10     | Required by Google ADK                 |
| TradingView MCP   | —          | Must be installed and accessible       |
| Gemini API Key    | —          | For `gemini-2.5-pro` via Google AI     |
| Voyage API Key    | —          | For RAG embedding and retrieval        |

---

## Getting Started

### 1. Clone and navigate

```bash
git clone <repo-url>
cd exemplar-platform-samples/python/platform/cost-observation/trading-agent
```

### 2. Create a virtual environment

**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `google-adk[mcp]` — Google ADK with MCP tool support
- `voyageai` — Voyage AI embedding client
- `chromadb` — Vector database for RAG
- `exemplar-harness-sdk` — Cost observability (optional, fails open)

### 4. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and fill in your keys:

| Variable           | Required | Description                                      |
| ------------------ | -------- | ------------------------------------------------ |
| `GEMINI_API_KEY`   | ✅       | Google AI API key for Gemini 2.5 Pro              |
| `VOYAGE_API_KEY`   | ✅       | Voyage AI API key (for RAG embedding + retrieval) |
| `MCP_VENV_PY`      | ✅       | Path to the TradingView MCP server's Python exe   |
| `MCP_SERVER_PATH`  | ✅       | Path to the TradingView MCP `server.py`           |
| `EXEMPLAR_API_KEY`  | ❌       | Exemplar integration-service key (for cost obs)   |
| `EXEMPLAR_BASE_URL` | ❌       | Exemplar service endpoint (default: localhost)     |
| `GLM_MODEL`        | ❌       | Override litellm model string                     |
| `MCP_TIMEOUT`      | ❌       | MCP subprocess timeout in seconds (default: 30)   |

### 5. Ingest RAG knowledge base (optional)

If you have domain documents (`.txt`, `.md`, `.csv`, `.json`, `.pdf`) to enhance the agent's responses:

```bash
# Ingest all files from a directory
python -m trading_agent.ingest ./docs/

# Ingest a single file
python -m trading_agent.ingest ./reports/q2_earnings.txt

# Custom chunk size and overlap
python -m trading_agent.ingest ./docs/ --chunk-size 800 --chunk-overlap 150
```

This creates a local ChromaDB database in `rag_data/chroma_db/` with Voyage AI embeddings.

---

## Running the Agent

### CLI

Run a single query from the command line:

```bash
python -m trading_agent.cli "What are the top gainers on BINANCE 1h right now?"
```

With no arguments, it runs a default query (`Give me a BINANCE 1h market snapshot.`).

### ADK Web UI

Start the ADK web interface from the **parent** of the `trading_agent` package:

```bash
adk web --no-reload --port 8001
```

Open [http://localhost:8001](http://localhost:8001) and select the **trading_agent** app.

> **Note:** `--no-reload` is required on Windows — the reloader's `ProactorEventLoop` subprocess transport throws `NotImplementedError`.

---

## Example Questions

### 💰 Prices & Quotes
```
What is the current price of BTCUSDT?
Get me a live quote for AAPL
What's the extended-hours price for TSLA?
```

### 📊 Market Overview
```
Give me a global market snapshot
What's the Bitcoin market pulse right now?
Show me a BINANCE 1h market snapshot
```

### 🚀 Screeners & Scanners
```
What are the top gainers on BINANCE 1h right now?
Show me the top losers on KUCOIN 15m
Find Bollinger squeeze setups on BINANCE 4h
Which coins have a strong buy rating on KUCOIN 5m?
Find volume breakout candidates on BINANCE 1h
Show me smart volume anomalies on KUCOIN
Scan for 3+ consecutive green candles on BINANCE 15m
```

### 🔍 Technical Analysis
```
Give me a full technical analysis for ETHUSDT on BINANCE 15m
Run a multi-timeframe analysis for SOLUSDT on KUCOIN
Give me a combined analysis for BTCUSDT on BINANCE 1D
Analyze the candlestick patterns for ADAUSDT on BINANCE 4h
Check volume confirmation for XRPUSDT on KUCOIN
```

### 📰 Sentiment & News
```
What's the market sentiment for Bitcoin?
Get me the latest financial news for AAPL
Show me crypto news and sentiment for ETH
```

### 📈 Backtesting
```
Backtest an RSI strategy on BTCUSDT BINANCE 1D
Compare RSI vs MACD vs Bollinger strategies on ETHUSDT
Run a walk-forward backtest for SOLUSDT with an SMA crossover strategy
```

### 🇪🇬 Egyptian Exchange (EGX)
```
Give me an EGX market overview
Screen EGX stocks with strong buy ratings
Show me EGX sector rotation analysis
Generate a trade plan for COMI on EGX
Run Fibonacci retracement for EFIH on EGX
Analyze the EGX30 index
```

### 📚 Knowledge Base (RAG)
```
What do our research notes say about momentum strategies?
Summarize the Q2 earnings analysis we ingested
What trading strategies are documented in our knowledge base?
```

> **Tip:** If you don't specify an exchange, the agent defaults to **BINANCE** for crypto and **NASDAQ** for stocks. If you don't specify a timeframe, it defaults to **1h** for intraday crypto and **1D** for stocks.

---

## Project Structure

```
trading-agent/
├── .env.example              # Environment variable template
├── requirements.txt          # Python dependencies
├── README.md
│
├── trading_agent/            # Main package
│   ├── __init__.py
│   ├── agent.py              # Root agent definition + Exemplar instrumentation
│   ├── cli.py                # CLI runner (async, with session scoping)
│   ├── config.py             # Configuration (env vars, defaults)
│   ├── ingest.py             # RAG document ingestion pipeline
│   ├── prompts.py            # System instruction / prompt templates
│   ├── rag.py                # Voyage AI + ChromaDB retrieval tool
│   └── tools.py              # MCP toolset factory
│
├── rag_data/                 # (git-ignored) ChromaDB persistent storage
│
├── test_agent.py             # Agent integration tests
├── test_agent2.py            # Additional agent tests
├── test_eval_run.py          # Evaluation run tests
├── check_mcp.py              # MCP server connectivity check
├── check_rag.py              # RAG pipeline verification
└── run_detectors_live.py     # Live cost-obs detector run
```

---

## Troubleshooting

| Problem | Solution |
| --- | --- |
| **Agent never calls a tool / loops** | Verify the MCP server is reachable. Check `MCP_VENV_PY` and `MCP_SERVER_PATH` in `.env` |
| **First call is slow** | The MCP server cold-starts (imports, loads coin lists). `MCP_TIMEOUT=30` covers it — increase if needed |
| **`ImportError: McpToolset`** | You installed `google-adk` without the MCP extra. Run `pip install "google-adk[mcp]"` |
| **`VOYAGE_API_KEY is not set`** | Add your Voyage API key to `.env` |
| **RAG returns no results** | Run the ingestion pipeline first: `python -m trading_agent.ingest ./docs/` |
| **`NotImplementedError` on Windows** | Use `--no-reload` flag when running `adk web` |

---

## Cost Observability (Optional)

The agent auto-instruments with the **Exemplar Harness SDK** when configured:

- **Composition metrics** — captured via the `genai` monkey-patch (covers ADK-on-Gemini natively)
- **Orchestration metrics** — LLM call counts, retries, tool call counts via ADK callbacks
- **Per-session scoping** — each CLI run gets its own session for cross-run detector analysis

Set `EXEMPLAR_API_KEY` and optionally `EXEMPLAR_BASE_URL` in `.env` to enable. The agent runs normally without these — observability **fails open**.