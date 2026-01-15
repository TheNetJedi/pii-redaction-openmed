"""Application configuration with environment variable support."""

import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Server (Used by API, kept here for shared config loader)
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "info"
    debug: bool = False

    # Model settings
    default_model: str = "openmed/OpenMed-PII-ClinicalE5-Small-33M-v1"
    model_cache_dir: str = "/tmp/redactx/models"
    device: str = "auto"  # auto, cpu, cuda

    # Processing settings
    max_file_size_mb: int = 50
    max_batch_size: int = 100
    default_confidence: float = 0.6
    default_method: str = "mask"
    use_smart_merging: bool = True

    # Security
    cors_origins: str = "*"
    api_key: str | None = None

    # Available models (lightweight to heavyweight)
    available_models: list[str] = [
        "openmed/OpenMed-PII-ClinicalE5-Small-33M-v1",  # 33M - Fastest
        "openmed/OpenMed-PII-SuperClinical-Small-44M-v1",  # 44M
        "openmed/OpenMed-PII-LiteClinical-Small-66M-v1",  # 66M
        "openmed/OpenMed-PII-FastClinical-Small-82M-v1",  # 82M
        "openmed/OpenMed-PII-ClinicalE5-Base-109M-v1",  # 109M
        "openmed/OpenMed-PII-BioClinicalModern-Base-149M-v1",  # 149M
        "openmed/OpenMed-PII-SuperClinical-Base-184M-v1",  # 184M
        "openmed/OpenMed-PII-SuperClinical-Large-434M-v1",  # 434M - Best accuracy
        "openmed/OpenMed-PII-QwenMed-XLarge-600M-v1",  # 600M - Largest
    ]

    # De-identification methods
    available_methods: list[str] = [
        "mask",  # Replace with [ENTITY_TYPE]
        "remove",  # Complete removal
        "replace",  # Synthetic data replacement
        "hash",  # Cryptographic hashing
        "shift_dates",  # Date shifting
    ]

    # Entity categories
    entity_categories: dict[str, list[str]] = {
        "identifiers": [
            "ssn",
            "passport",
            "medical_record_number",
            "credit_debit_card",
            "api_key",
            "password",
            "account_number",
            "license_plate",
            "device_id",
            "certificate",
            "driver_license",
            "national_id",
            "insurance_id",
            "tax_id",
            "vehicle_id",
            "biometric",
        ],
        "personal": [
            "first_name",
            "last_name",
            "full_name",
            "date_of_birth",
            "age",
            "gender",
            "occupation",
            "blood_type",
            "nationality",
            "ethnicity",
            "religion",
            "marital_status",
            "education",
            "photo",
        ],
        "contact": ["phone_number", "fax_number", "email", "pager"],
        "location": [
            "street_address",
            "city",
            "state",
            "postcode",
            "country",
            "gps_coordinates",
        ],
        "network": ["ipv4", "ipv6", "mac_address", "url"],
        "temporal": ["date", "time", "duration"],
        "organization": ["organization"],
    }

    class Config:
        env_prefix = "REDACTX_"
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
