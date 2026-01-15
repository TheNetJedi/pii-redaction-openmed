"""Document handling API endpoints."""

import logging
from typing import Annotated

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Response

from redac_core.schemas import (
    RedactionConfig,
    DocumentRedactionResult,
    DocumentAnalysisResult,
    RedactionMethod,
    OutputFormat,
)
from redac_core.services import get_redaction_service, get_document_handler
from redac_core.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()


async def _read_and_validate(file: UploadFile) -> bytes:
    """Validate and read file content."""
    handler = get_document_handler()

    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename required")

    if not handler.is_supported(file.filename):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Supported: {', '.join(handler.SUPPORTED_EXTENSIONS)}",
        )

    content = await file.read()
    file_size_mb = len(content) / (1024 * 1024)

    if file_size_mb > settings.max_file_size_mb:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum: {settings.max_file_size_mb}MB",
        )

    return content


def _parse_entity_types(entity_types: str | None) -> list[str] | None:
    """Parse comma-separated entity types."""
    if not entity_types:
        return None
    return [t.strip() for t in entity_types.split(",") if t.strip()]


def _get_content_type(filename: str) -> str:
    """Get MIME type for filename."""
    ext = filename.split(".")[-1].lower()
    types = {
        "pdf": "application/pdf",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "txt": "text/plain",
        "md": "text/markdown",
        "json": "application/json",
    }
    return types.get(ext, "application/octet-stream")


@router.post(
    "/documents/redact",
    response_model=DocumentRedactionResult,
    summary="Redact a document",
    description="Upload and redact a document (PDF, DOCX, TXT). Returns download information.",
)
async def redact_document(
    file: Annotated[UploadFile, File(description="Document to redact")],
    method: Annotated[str, Form()] = "mask",
    confidence_threshold: Annotated[float, Form()] = 0.6,
    model: Annotated[str, Form()] = None,
    include_mapping: Annotated[bool, Form()] = False,
    output_format: Annotated[str, Form()] = "same",
    entity_types: Annotated[str | None, Form()] = None,
) -> Response:
    """Redact a document and return the redacted file."""
    content = await _read_and_validate(file)
    handler = get_document_handler()

    try:
        # Extract text
        text = handler.extract_text(content, file.filename)
        if not text.strip():
            raise HTTPException(status_code=400, detail="No text content found")

        # Config
        config = RedactionConfig(
            model=model or settings.default_model,
            confidence_threshold=confidence_threshold,
            method=RedactionMethod(method),
            include_mapping=include_mapping,
            output_format=OutputFormat(output_format),
            entity_types=_parse_entity_types(entity_types),
        )

        # Redact
        service = get_redaction_service()
        result = service.redact_text(text, config)

        # Create document
        redacted_content, redacted_filename = handler.create_redacted_document(
            content,
            file.filename,
            result.redacted_text,
            output_format if output_format != "same" else None,
            entities=result.entities,
            method=method,
        )

        content_type = _get_content_type(redacted_filename)

        logger.info(
            f"Redacted {file.filename} -> {redacted_filename} "
            f"({result.entity_count} entities)"
        )

        return Response(
            content=redacted_content,
            media_type=content_type,
            headers={
                "Content-Disposition": f'attachment; filename="{redacted_filename}"',
                "X-Entity-Count": str(result.entity_count),
                "X-Original-Filename": file.filename,
            },
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Redaction failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Redaction failed: {str(e)}")


@router.post(
    "/documents/extract-text",
    summary="Extract text from document",
    description="Extract text content from a document without redacting.",
)
async def extract_text(
    file: Annotated[UploadFile, File(description="Document to extract text from")],
) -> dict:
    """Extract text from a document."""
    content = await _read_and_validate(file)
    handler = get_document_handler()

    try:
        text = handler.extract_text(content, file.filename)
        return {
            "filename": file.filename,
            "text": text,
            "character_count": len(text),
            "word_count": len(text.split()),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/documents/analyze",
    response_model=DocumentAnalysisResult,
    summary="Analyze document for PII",
    description="Scan document and return detected entity statistics without redacting.",
)
async def analyze_document(
    file: Annotated[UploadFile, File(description="Document to analyze")],
    model: Annotated[str, Form()] = None,
) -> DocumentAnalysisResult:
    """Analyze document and return PII statistics."""
    content = await _read_and_validate(file)
    handler = get_document_handler()

    try:
        text = handler.extract_text(content, file.filename)
        if not text.strip():
            raise HTTPException(status_code=400, detail="No text content found")

        config = RedactionConfig(model=model or settings.default_model)
        service = get_redaction_service()
        entities = service.extract_entities(text, config)

        stats = {}
        for e in entities:
            stats[e.label] = stats.get(e.label, 0) + 1

        return DocumentAnalysisResult(
            filename=file.filename,
            total_entities=len(entities),
            by_type=stats,
            all_types=sorted(list(stats.keys())),
        )
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/documents/supported-formats",
    summary="Get supported formats",
    description="List supported document formats for upload.",
)
async def get_supported_formats() -> dict:
    """Get list of supported document formats."""
    handler = get_document_handler()
    return {
        "supported_extensions": list(handler.SUPPORTED_EXTENSIONS),
        "max_file_size_mb": settings.max_file_size_mb,
    }
