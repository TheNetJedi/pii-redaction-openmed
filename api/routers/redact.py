"""Redaction API endpoints."""

import logging
from fastapi import APIRouter, HTTPException

from redac_core.schemas import (
    TextRedactionRequest,
    BatchRedactionRequest,
    RedactionResult,
    BatchRedactionResult,
    RedactionConfig,
    EntityInfo,
)
from redac_core.services import get_redaction_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/redact/text",
    response_model=RedactionResult,
    summary="Redact PII from text",
    description="Detect and redact PII entities from raw text using the configured method.",
)
async def redact_text(request: TextRedactionRequest) -> RedactionResult:
    """Redact PII from raw text."""
    try:
        service = get_redaction_service()
        result = service.redact_text(request.text, request.config)
        logger.info(f"Redacted text with {result.entity_count} entities using {result.method}")
        return result
    except Exception as e:
        logger.error(f"Text redaction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/redact/batch",
    response_model=BatchRedactionResult,
    summary="Batch redact multiple texts",
    description="Process multiple texts in a single request for efficient bulk redaction.",
)
async def redact_batch(request: BatchRedactionRequest) -> BatchRedactionResult:
    """Redact PII from multiple texts."""
    try:
        service = get_redaction_service()
        result = service.redact_batch(request.texts, request.ids, request.config)
        logger.info(
            f"Batch redaction: {result.successful_items}/{result.total_items} successful, "
            f"{result.total_entities} entities in {result.processing_time_seconds}s"
        )
        return result
    except Exception as e:
        logger.error(f"Batch redaction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/extract",
    response_model=list[EntityInfo],
    summary="Extract PII entities",
    description="Extract PII entities from text without redacting. Useful for preview.",
)
async def extract_entities(request: TextRedactionRequest) -> list[EntityInfo]:
    """Extract PII entities without redacting."""
    try:
        service = get_redaction_service()
        entities = service.extract_entities(request.text, request.config)
        logger.info(f"Extracted {len(entities)} entities")
        return entities
    except Exception as e:
        logger.error(f"Entity extraction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/preview",
    response_model=RedactionResult,
    summary="Preview redaction",
    description="Preview redaction results without committing. Same as /redact/text but semantic difference.",
)
async def preview_redaction(request: TextRedactionRequest) -> RedactionResult:
    """Preview redaction without committing."""
    # Same as redact_text but semantically different
    return await redact_text(request)
