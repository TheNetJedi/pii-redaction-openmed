# PII Redaction Tool 🛡️

**Production-grade PII redaction powered by OpenMed**

PII Redaction Tool is a complete, containerized solution for detecting and redacting Personally Identifiable Information (PII) from documents. It supports 54 entity types, 5 redaction methods, and is fully HIPAA/GDPR compliant.

## Features

- 🔍 **54 PII Entity Types** - Names, SSN, dates, addresses, medical records, API keys, and more
- 📄 **Multiple Formats** - PDF, DOCX, TXT, MD
- 🎛️ **5 Redaction Methods** - Mask, remove, replace, hash, shift dates
- ⚡ **Lightweight by Default** - Uses 33M parameter model for fast inference
- 🐳 **Container Ready** - Stateless, runs from Docker
- 💻 **CLI Mode** - Full functionality from command line
- 🌐 **Modern Web UI** - TanStack Start + React

## Quick Start

### Using Docker Compose

```bash
# Production
docker-compose up -d

# Development (with hot reload)
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

Access:
- Web UI: http://localhost:3000
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Using CLI

```bash
# Install CLI
cd cli && uv pip install -e .

# Redact text
redactx redact --text "Patient John Doe, SSN: 123-45-6789"

# Redact file
redactx redact --input patient_note.txt --output redacted.txt --method mask

# Batch process
redactx batch ./input_dir/ ./output_dir/ --method mask --pattern "*.txt"

# Extract entities only
redactx extract --text "John Doe, DOB: 01/15/1985" --json
```

### Local Development

**Core (Required):**
```bash
# Install core library first
cd core
uv pip install -e .
```

**Backend (API):**
```bash
cd api
uv venv && source .venv/bin/activate
# Core is required (install via pip or ensure sys.path resolution)
uv pip install -e ../core
uv pip install -e .
uvicorn main:app --reload
```

**Frontend (Web):**
```bash
cd web
bun install
bun run dev
```

## Configuration

Environment variables (prefix with `REDACTX_`):

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | API host |
| `PORT` | `8000` | API port |
| `DEFAULT_MODEL` | `openmed/OpenMed-PII-ClinicalE5-Small-33M-v1` | Default model |
| `DEFAULT_METHOD` | `mask` | Default redaction method |
| `DEFAULT_CONFIDENCE` | `0.6` | Default confidence threshold |
| `DEVICE` | `auto` | Inference device (auto/cpu/cuda) |
| `MAX_FILE_SIZE_MB` | `50` | Maximum upload size |
| `CORS_ORIGINS` | `*` | Allowed CORS origins |

## Available Models

| Model | Size | Speed | Accuracy |
|-------|------|-------|----------|
| ClinicalE5-Small ★ | 33M | Fastest | Good |
| FastClinical-Small | 82M | Fast | Better |
| SuperClinical-Large | 434M | Slower | Best |

## Redaction Methods

| Method | Description | Example |
|--------|-------------|---------|
| `mask` | Replace with `[ENTITY_TYPE]` | John Doe → `[first_name] [last_name]` |
| `remove` | Completely remove | John Doe → ` ` |
| `replace` | Synthetic data | John Doe → Jane Smith |
| `hash` | Cryptographic hash | John Doe → `first_name_7e8c729e` |
| `shift_dates` | Shift by N days | 01/15/2025 → 07/14/2025 |

## API Endpoints

### Redaction
- `POST /api/v1/redact/text` - Redact raw text
- `POST /api/v1/redact/batch` - Batch redact multiple texts
- `POST /api/v1/extract` - Extract entities without redacting

### Documents
- `POST /api/v1/documents/redact` - Upload and redact document
- `POST /api/v1/documents/extract-text` - Extract text from document

### Configuration
- `GET /api/v1/config/models` - List available models
- `GET /api/v1/config/methods` - List redaction methods
- `GET /api/v1/config/defaults` - Get default configuration

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      PII Redaction Tool                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│       ┌───────────┐         ┌──────────────┐                │
│       │    Web    │───────▶ │     API      │                │
│       └───────────┘         └──────┬───────┘                │
│                                    │                        │
│                                    ▼                        │
│       ┌───────────┐         ┌──────────────┐                │
│       │    CLI    │───────▶ │  Redac Core  │                │
│       └───────────┘         │  (Services)  │                │
│                             └──────────────┘                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Tech Stack

- **Backend**: FastAPI, OpenMed, PyMuPDF, python-docx
- **Frontend**: TanStack Start, React 19, Tailwind CSS
- **CLI**: Typer, Rich
- **Container**: Docker, Docker Compose

## License

MIT License

## Credits

This project relies heavily on the excellent work by [Maziyar Panahi](https://github.com/maziyarpanahi) and the [OpenMed](https://github.com/maziyarpanahi/openmed) library.

- **OpenMed Library**: [https://github.com/maziyarpanahi/openmed](https://github.com/maziyarpanahi/openmed)
- **PII Detection Guide**: [PII Detection Complete Guide](https://github.com/maziyarpanahi/openmed/blob/master/examples/notebooks/PII_Detection_Complete_Guide.ipynb)
- **Maziyar Panahi**: [GitHub Profile](https://github.com/maziyarpanahi)

