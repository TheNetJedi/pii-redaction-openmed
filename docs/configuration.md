# Configuration Guide

The PII Redaction Tool is highly configurable to suit different clinical and privacy requirements. Configuration is managed via Environment Variables or runtime request parameters.

## Environment Variables

These variables control the global behavior of the backend API.

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `REDACTX_HOST` | String | `0.0.0.0` | Host interface to bind the API. |
| `REDACTX_PORT` | Integer | `8000` | Port to listen on. |
| `REDACTX_DEFAULT_MODEL` | String | `openmed/OpenMed-PII-ClinicalE5-Small-33M-v1` | The default HuggingFace model for PII detection. |
| `REDACTX_DEVICE` | String | `auto` | `cuda` (GPU), `cpu`, or `mps` (Mac). `auto` selects GPU if available. |
| `REDACTX_DEBUG` | Boolean | `false` | Enable debug logs and auto-reload. |
| `REDACTX_MAX_FILE_SIZE_MB` | Integer | `50` | Maximum allowed upload size in Megabytes. |

---

## Redaction Methods

The tool supports 4 distinct redaction strategies. These can be selected locally in the UI or passed to the API.

### 1. Mask (Default)
**Behavior**: Replaces the PII text with a placeholder or black box.
- **Text Output**: `[PERSON]`, `[DATE]`
- **PDF Output**: **Black Box** covering the text area.
- **Use Case**: General visual redaction where the document layout must be preserved but content hidden.

### 2. Remove
**Behavior**: Completely erases the PII.
- **Text Output**: `       ` (Whitespace)
- **PDF Output**: **White Box** (appears as if text was lifted off the page).
- **Use Case**: Clean copies where redaction shouldn't be distracting (e.g. "Whiteout").

### 3. Replace
**Behavior**: Overlays the text with its Entity Type label.
- **Text Output**: `[PERSON]`
- **PDF Output**: **Light Gray Box** with text like `[PERSON]` or `[DATE]`.
- **Use Case**: Semantic analysis where knowing *what* was there is important (e.g. "On [DATE], [PERSON] visited...").

### 4. Hash
**Behavior**: Replaces PII with a consistent hashed value.
- **Text Output**: `md5_hash_prefix`
- **PDF Output**: **Gray Box** containing the hash code.
- **Use Case**: Data linkage studies where the same patient needs to be identified across documents without revealing their identity.

---

## Supported Models

The system is powered by the **OpenMed** family of models, optimized for clinical NLP.

1. **ClinicalE5-Small (33M)**
   - **Recommended Default**.
   - Ultra-fast CPU inference (~50ms/page).
   - Good accuracy on standard clinical notes.

2. **FastClinical-Small (82M)**
   - Better context understanding.
   - Slower on CPU, recommended with GPU.

3. **SuperClinical-Large (434M)**
   - Highest accuracy.
   - Requires GPU for reasonable latency.

*To extract the best performance, map the `REDACTX_DEFAULT_MODEL` to a local path or cache volume to avoid re-downloading from HuggingFace.*
