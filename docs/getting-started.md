# Getting Started with PII Redaction Tool

This guide helps you set up PII Redaction Tool for production use or local development.

## Prerequisites

- **Docker & Docker Compose** (Recommended for production)
- **Python 3.11+** (For local backend/CLI)
- **Node.js 20+ & Bun** (For local frontend)
- **NVIDIA GPU** (Optional, for accelerated inference)

---

## 🚀 Quick Start (Docker)

The fastest way to run the PII Redaction Tool is using Docker Compose. This spins up the API, Frontend, and configured networks.

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/pii-redaction-tool.git
   cd pii-redaction-tool
   ```

2. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env if needed (normally defaults are fine)
   ```

3. **Start Services**
   ```bash
   docker-compose up -d
   ```

4. **Access the App**
   - **Web UI:** [http://localhost:3000](http://localhost:3000)
   - **API Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🛠️ Local Development

If you want to contribute or modify the code, run the services locally.

### 1. Backend API

The backend is built with FastAPI and manages the PII detection models.

```bash
cd api

# Create virtual environment
uv venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install dependencies
uv pip install -e .

# Run dev server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Frontend Web App

The frontend is a modern React application powered by TanStack Start.

```bash
cd web

# Install dependencies
bun install

# Start dev server
bun run dev
```
The UI will be available at [http://localhost:3000](http://localhost:3000).

### 3. CLI Tool

The CLI allows you to redact text and files from the command line.

```bash
cd cli

# Install
uv pip install -e .

# Usage
redactx --help
```

---

## ⚙️ Configuration

The application is configured via environment variables. See `docs/configuration.md` for a full list of options.

### Common Settings (in `.env`)

| Variable | Description | Default |
|----------|-------------|---------|
| `REDACTX_DEFAULT_MODEL` | PII Model to load | `openmed/OpenMed-PII-ClinicalE5-Small-33M-v1` |
| `REDACTX_DEVICE` | Inference device | `auto` (detects CUDA) |
| `REDACTX_MAX_FILE_SIZE_MB` | Upload limit | `50` |

---

## 🧪 Testing

To run the test suite:

```bash
# Backend Tests
cd api
pytest

# CLI Tests
cd cli
pytest
```
