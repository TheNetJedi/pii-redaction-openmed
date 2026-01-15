# Architecture & Design

The PII Redaction Tool follows a **Stateless Microservices Architecture** specifically designed for high-security environments like healthcare.

## High-Level Overview

```mermaid
graph LR
    User[End User] -->|HTTPS| Web[Web App (React)]
    Web -->|JSON/Multipart| API[FastAPI Backend]
    
    subgraph Core Engine [Private Container]
        API -->|Bytes| DocHandler[Document Handler]
        DocHandler -->|Text| Model[OpenMed LLM]
        Model -->|Entities| DocHandler
        DocHandler -->|Redacted Bytes| API
    end
    
    API -->|Download| Web
```

---

## Core Components

### 1. Web Frontend (React)
- **Framework**: TanStack Start (React 19).
- **Function**: Provides the visual interface, state management, and file previewing using Blob URLs.
- **Privacy**: The frontend never stores data. It streams the file to the backend and displays the returned result directly in memory.

### 2. Backend API (FastAPI)
- **Framework**: FastAPI (Python).
- **Function**: Routing, validation, and orchestration.
- **Statelessness**: The API does not have a database. It processes requests in-memory and destroys all artifacts immediately after the response is sent.

### 3. OpenMed Engine
- **Library**: `openmed` (Transformers/PyTorch).
- **Function**: Named Entity Recognition (NER) for identifying PII.
- **Performance**: Uses `onnx` or `torch` quantization for fast CPU inference.

### 4. Document Handler
- **Libraries**: `PyMuPDF` (PDF), `python-docx` (Word).
- **Function**: Handles the logic of parsing files and applying in-place redactions.
- **Strategy**: 
    - For PDFs, it does NOT convert to images (OCR). It manipulates the PDF structure directly to draw redaction annotations, preserving text searchability (for non-redacted parts) and original formatting.

---

## Security & compliance

### Zero Retention Policy
By design, the PII Redaction Tool has **Zero Persistence**:
- No Database.
- No Storage Buckets (S3/Blob).
- No Logs containing PII (Inputs are masked in logs).
- Temp files are written to ephemeral `/tmp` storage (if RAM is exceeded) and wiped instantly.

### Air-Gapped Readiness
The docker container is self-sufficient. Models can be pre-baked into the image, allowing the system to run without any internet connection, ensuring no data ever leaves the secure network.
