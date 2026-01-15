"""Configuration API endpoints."""

import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from redac_core.schemas import ModelInfo, EntityTypeInfo
from redac_core.config import get_settings
from redac_core.services import get_redaction_service

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()


class UpdateModelRequest(BaseModel):
    model_id: str


# Model metadata
MODEL_INFO = {
    "openmed/OpenMed-PII-ClinicalE5-Small-33M-v1": {
        "name": "ClinicalE5 Small",
        "size": "33M",
        "description": "Fastest model, good accuracy. Best for quick processing.",
        "recommended": True,
    },
    "openmed/OpenMed-PII-SuperClinical-Small-44M-v1": {
        "name": "SuperClinical Small",
        "size": "44M",
        "description": "Compact model with improved clinical text handling.",
        "recommended": False,
    },
    "openmed/OpenMed-PII-LiteClinical-Small-66M-v1": {
        "name": "LiteClinical Small",
        "size": "66M",
        "description": "Lightweight model optimized for clinical notes.",
        "recommended": False,
    },
    "openmed/OpenMed-PII-FastClinical-Small-82M-v1": {
        "name": "FastClinical Small",
        "size": "82M",
        "description": "Fast inference with better accuracy than smaller models.",
        "recommended": False,
    },
    "openmed/OpenMed-PII-ClinicalE5-Base-109M-v1": {
        "name": "ClinicalE5 Base",
        "size": "109M",
        "description": "Balanced model for general use.",
        "recommended": False,
    },
    "openmed/OpenMed-PII-BioClinicalModern-Base-149M-v1": {
        "name": "BioClinicalModern Base",
        "size": "149M",
        "description": "Modern architecture trained on biomedical clinical text.",
        "recommended": False,
    },
    "openmed/OpenMed-PII-SuperClinical-Base-184M-v1": {
        "name": "SuperClinical Base",
        "size": "184M",
        "description": "Enhanced clinical text understanding.",
        "recommended": False,
    },
    "openmed/OpenMed-PII-SuperClinical-Large-434M-v1": {
        "name": "SuperClinical Large",
        "size": "434M",
        "description": "Best accuracy, recommended for production with resources.",
        "recommended": True,
    },
    "openmed/OpenMed-PII-QwenMed-XLarge-600M-v1": {
        "name": "QwenMed XLarge",
        "size": "600M",
        "description": "Largest model, maximum accuracy, requires significant resources.",
        "recommended": False,
    },
}


@router.get(
    "/config/models",
    response_model=list[ModelInfo],
    summary="List available models",
    description="Get list of available PII detection models with metadata.",
)
async def list_models() -> list[ModelInfo]:
    """List available models."""
    models = []
    for model_id, info in MODEL_INFO.items():
        models.append(
            ModelInfo(
                id=model_id,
                name=info["name"],
                size=info["size"],
                description=info["description"],
                recommended=info["recommended"],
            )
        )
    return sorted(models, key=lambda m: m.id)


@router.get(
    "/config/entities",
    response_model=EntityTypeInfo,
    summary="List entity types",
    description="Get list of supported PII entity types organized by category.",
)
async def list_entity_types() -> EntityTypeInfo:
    """List supported entity types."""
    all_types = []
    for types in settings.entity_categories.values():
        all_types.extend(types)

    return EntityTypeInfo(
        categories=settings.entity_categories,
        all_types=sorted(set(all_types)),
    )


@router.get(
    "/config/methods",
    summary="List redaction methods",
    description="Get list of available de-identification methods.",
)
async def list_methods() -> dict:
    """List available redaction methods."""
    return {
        "methods": [
            {
                "id": "mask",
                "name": "Mask",
                "description": "Replace PII with [ENTITY_TYPE] placeholders",
                "example": "John Doe → [first_name] [last_name]",
            },
            {
                "id": "remove",
                "name": "Remove",
                "description": "Completely remove PII from text",
                "example": "John Doe → ",
            },
            {
                "id": "replace",
                "name": "Replace",
                "description": "Replace PII with synthetic/fake data",
                "example": "John Doe → Jane Smith",
            },
            {
                "id": "hash",
                "name": "Hash",
                "description": "Replace PII with cryptographic hash (deterministic)",
                "example": "John Doe → first_name_7e8c729e last_name_3013b18f",
            },
            {
                "id": "shift_dates",
                "name": "Shift Dates",
                "description": "Shift all dates by a fixed number of days",
                "example": "01/15/2024 → 07/14/2024 (shifted by 180 days)",
            },
        ],
        "default": settings.default_method,
    }


@router.get(
    "/config/defaults",
    summary="Get default configuration",
    description="Get the default configuration values.",
)
async def get_defaults() -> dict:
    """Get default configuration."""
    service = get_redaction_service()
    return {
        "model": service.active_model_name,
        "method": settings.default_method,
        "confidence_threshold": settings.default_confidence,
        "use_smart_merging": settings.use_smart_merging,
        "device": settings.device,
        "max_file_size_mb": settings.max_file_size_mb,
        "max_batch_size": settings.max_batch_size,
    }


@router.post(
    "/config/model",
    summary="Set active model",
    description="Update the active PII detection model used for shared requests.",
)
async def set_active_model(request: UpdateModelRequest):
    """Set the active model."""
    if request.model_id not in MODEL_INFO:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown model: {request.model_id}. Available: {list(MODEL_INFO.keys())}",
        )

    service = get_redaction_service()
    service.set_active_model(request.model_id)
    
    return {
        "status": "updated",
        "model": request.model_id,
        "info": MODEL_INFO[request.model_id],
    }
