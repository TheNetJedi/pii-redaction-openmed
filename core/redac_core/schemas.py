"""Pydantic schemas for request/response validation."""

from enum import Enum
from pydantic import BaseModel, Field


class RedactionMethod(str, Enum):
    """Available de-identification methods."""

    MASK = "mask"
    REMOVE = "remove"
    REPLACE = "replace"
    HASH = "hash"
    SHIFT_DATES = "shift_dates"


class DeviceType(str, Enum):
    """Inference device types."""

    AUTO = "auto"
    CPU = "cpu"
    CUDA = "cuda"


class OutputFormat(str, Enum):
    """Output format options."""

    SAME = "same"  # Same as input
    TXT = "txt"
    JSON = "json"


# ============================================================================
# Request Schemas
# ============================================================================


class RedactionConfig(BaseModel):
    """Configuration for PII redaction."""

    # Model selection
    model: str = Field(
        default="openmed/OpenMed-PII-ClinicalE5-Small-33M-v1",
        description="HuggingFace model ID for PII detection",
    )

    # Detection settings
    confidence_threshold: float = Field(
        default=0.6, ge=0.0, le=1.0, description="Minimum confidence (0.0-1.0)"
    )
    use_smart_merging: bool = Field(
        default=True, description="Enable smart entity merging for better accuracy"
    )

    # Redaction method
    method: RedactionMethod = Field(
        default=RedactionMethod.MASK, description="De-identification method"
    )
    date_shift_days: int | None = Field(
        default=None, description="Days to shift dates (for shift_dates method)"
    )

    # Entity filtering
    entity_types: list[str] | None = Field(
        default=None, description="Only process these entity types"
    )
    exclude_entity_types: list[str] | None = Field(
        default=None, description="Exclude these entity types"
    )

    # Output options
    include_mapping: bool = Field(
        default=False, description="Include re-identification mapping"
    )
    output_format: OutputFormat = Field(
        default=OutputFormat.SAME, description="Output file format"
    )

    # Advanced
    device: DeviceType = Field(
        default=DeviceType.AUTO, description="Inference device"
    )


class TextRedactionRequest(BaseModel):
    """Request to redact raw text."""

    text: str = Field(..., description="Text to redact", min_length=1)
    config: RedactionConfig = Field(default_factory=RedactionConfig)


class BatchRedactionRequest(BaseModel):
    """Request to redact multiple texts."""

    texts: list[str] = Field(
        ..., description="List of texts to redact", min_length=1, max_length=100
    )
    ids: list[str] | None = Field(
        default=None, description="Optional IDs for each text"
    )
    config: RedactionConfig = Field(default_factory=RedactionConfig)


# ============================================================================
# Response Schemas
# ============================================================================


class EntityInfo(BaseModel):
    """Information about a detected PII entity."""

    text: str = Field(..., description="Original entity text")
    label: str = Field(..., description="Entity type/label")
    confidence: float = Field(..., description="Detection confidence")
    start: int = Field(..., description="Start position in text")
    end: int = Field(..., description="End position in text")
    redacted_text: str | None = Field(
        default=None, description="Redacted replacement text"
    )


class RedactionResult(BaseModel):
    """Result of a redaction operation."""

    original_text: str = Field(..., description="Original input text")
    redacted_text: str = Field(..., description="Redacted output text")
    entities: list[EntityInfo] = Field(
        default_factory=list, description="Detected entities"
    )
    entity_count: int = Field(..., description="Number of entities detected")
    mapping: dict[str, str] | None = Field(
        default=None, description="Re-identification mapping (if requested)"
    )
    method: str = Field(..., description="De-identification method used")
    model: str = Field(..., description="Model used for detection")
    confidence_threshold: float = Field(..., description="Confidence threshold used")


class BatchRedactionResult(BaseModel):
    """Result of a batch redaction operation."""

    results: list[RedactionResult] = Field(..., description="Individual results")
    total_items: int = Field(..., description="Total items processed")
    successful_items: int = Field(..., description="Successfully processed items")
    failed_items: int = Field(..., description="Failed items")
    total_entities: int = Field(..., description="Total entities detected")
    processing_time_seconds: float = Field(..., description="Total processing time")


class DocumentRedactionResult(BaseModel):
    """Result of document redaction with download info."""

    document_id: str = Field(..., description="Unique document ID")
    original_filename: str = Field(..., description="Original filename")
    redacted_filename: str = Field(..., description="Redacted filename")
    entity_count: int = Field(..., description="Number of entities redacted")
    download_url: str = Field(..., description="URL to download redacted document")
    expires_at: str | None = Field(
        default=None, description="Download URL expiration"
    )


class DocumentAnalysisResult(BaseModel):
    """Result of document scanning."""

    filename: str = Field(..., description="Filename")
    total_entities: int = Field(..., description="Total entities found")
    by_type: dict[str, int] = Field(..., description="Count by entity type")
    all_types: list[str] = Field(..., description="List of detected types")


# ============================================================================
# Config/Info Schemas
# ============================================================================


class ModelInfo(BaseModel):
    """Information about an available model."""

    id: str = Field(..., description="Model ID")
    name: str = Field(..., description="Display name")
    size: str = Field(..., description="Model size (e.g., 33M, 434M)")
    description: str = Field(..., description="Model description")
    recommended: bool = Field(default=False, description="Recommended model flag")


class EntityTypeInfo(BaseModel):
    """Information about entity types."""

    categories: dict[str, list[str]] = Field(
        ..., description="Entity types by category"
    )
    all_types: list[str] = Field(..., description="All available entity types")


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    model_loaded: bool = Field(..., description="Whether model is loaded")
    default_model: str = Field(..., description="Default model in use")


class ErrorResponse(BaseModel):
    """Error response."""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: dict | None = Field(default=None, description="Additional details")
