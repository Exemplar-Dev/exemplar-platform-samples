# Python samples

Uses the published [`exemplar-harness-sdk`](https://pypi.org/project/exemplar-harness-sdk/).

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # EXEMPLAR_API_KEY=eis_…

python -m platform.memory
python -m platform.skills
python -m platform.prompts
python -m platform.hitl
python -m relay.evaluate
python -m relay.langchain_middleware

pip install -r requirements-frameworks.txt
python -m frameworks.langchain_mcp
python -m frameworks.agno_mcp
```

Docs: https://docs.exemplar.dev/marshal/sdk/live-examples
