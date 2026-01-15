# RedactX API

Production-grade PII redaction API powered by OpenMed.

## Quick Start

```bash
uv venv && source .venv/bin/activate
# Install Core dependency first
uv pip install -e ../core
uv pip install -e .
uvicorn main:app --reload
```

## Endpoints

- `POST /api/v1/redact/text` - Redact raw text
- `POST /api/v1/documents/redact` - Upload and redact document
- `GET /health` - Health check
- `GET /docs` - API documentation

See main README.md for full documentation.
