"""RedacX Core Logic."""

from .config import get_settings
from .services import get_redaction_service, get_document_handler

__all__ = ["get_settings", "get_redaction_service", "get_document_handler"]
