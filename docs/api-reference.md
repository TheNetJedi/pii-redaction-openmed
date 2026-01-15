# API Reference

The PII Redaction Tool API is a RESTful service built with FastAPI. It provides endpoints for text and document redaction, entity extraction, and configuration.

**Base URL**: `http://localhost:8000/api/v1`

---

## 🔒 Redaction Endpoints

### 1. Redact Text
Redacts PII from a raw text string.

- **Endpoint**: `POST /redact/text`
- **Content-Type**: `application/json`

#### Request
```json
{
  "text": "Patient John Doe was admitted on 01/15/2024.",
  "config": {
    "method": "mask",
    "confidence_threshold": 0.6,
    "entity_types": ["PERSON", "DATE"]
  }
}
```

#### Response
```json
{
  "original_text": "Patient John Doe was admitted on 01/15/2024.",
  "redacted_text": "Patient [PERSON] was admitted on [DATE].",
  "entity_count": 2,
  "entities": [
    {
      "text": "John Doe",
      "label": "PERSON",
      "start": 8,
      "end": 16,
      "score": 0.98
    }
  ]
}
```

### 2. Redact Document
Uploads and redraws a document (PDF, DOCX, TXT).

- **Endpoint**: `POST /documents/redact`
- **Content-Type**: `multipart/form-data`

#### Parameters
- `file`: (File, Required) The document to redact.
- `method`: (String) `mask`, `remove`, `replace`, `hash`.
- `confidence_threshold`: (Float) 0.0 to 1.0.

#### Example (cURL)
```bash
curl -X POST "http://localhost:8000/api/v1/documents/redact" \
  -F "file=@/path/to/patient_record.pdf" \
  -F "method=mask" \
  -O
```
*Returns the redacted file as a binary stream.*

---

## 🔍 Extraction Endpoints

### 1. Extract Entities
Returns detected entities without redacting the text.

- **Endpoint**: `POST /extract`
- **Content-Type**: `application/json`

#### Request
```json
{
  "text": "Contact info: test@example.com (555) 123-4567"
}
```

#### Response
```json
[
  {
    "text": "test@example.com",
    "label": "EMAIL_ADDRESS",
    "score": 0.95
  },
  {
    "text": "(555) 123-4567",
    "label": "PHONE_NUMBER",
    "score": 0.92
  }
]
```

---

## ⚙️ Configuration Endpoints

### 1. List Models
Returns a list of available PII detection models.

- **Endpoint**: `GET /config/models`

### 2. List Methods
Returns supported redaction methods.

- **Endpoint**: `GET /config/methods`

---

## Error Handling

The API uses standard HTTP status codes:
- `200`: Success
- `400`: Bad Request (invalid file type, config)
- `422`: Validation Error (missing fields)
- `500`: Internal Server Error

All errors return a JSON object:
```json
{
  "detail": "Error description..."
}
```
