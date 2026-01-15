"""Core redaction service using OpenMed PII detection."""

import time
import logging
import hashlib
from typing import Any
from functools import lru_cache

from openmed import extract_pii, deidentify, PIIEntity, DeidentificationResult
from redac_core.schemas import (
    RedactionConfig,
    RedactionResult,
    EntityInfo,
    BatchRedactionResult,
    RedactionMethod,
)
from redac_core.config import get_settings

logger = logging.getLogger(__name__)


class RedactionService:
    """Service for PII detection and de-identification."""

    def __init__(self):
        self.settings = get_settings()
        self._model_cache: dict[str, Any] = {}
        # Runtime configurable default model
        self.active_model_name = self.settings.default_model
        logger.info(f"RedactionService initialized with default model: {self.active_model_name}")

    def set_active_model(self, model_name: str):
        """Update the active default model."""
        self.active_model_name = model_name
        logger.info(f"Active model switched to: {model_name}")

    def _get_device(self, device: str) -> str:
        """Determine the device to use for inference."""
        if device == "auto":
            try:
                import torch
                return "cuda" if torch.cuda.is_available() else "cpu"
            except ImportError:
                return "cpu"
        return device

    def _filter_entities(
        self,
        entities: list[PIIEntity],
        include_types: list[str] | None,
        exclude_types: list[str] | None,
    ) -> list[PIIEntity]:
        """Filter entities by type inclusion/exclusion."""
        filtered = entities

        if include_types:
            include_set = set(t.lower() for t in include_types)
            filtered = [e for e in filtered if e.label.lower() in include_set]

        if exclude_types:
            exclude_set = set(t.lower() for t in exclude_types)
            filtered = [e for e in filtered if e.label.lower() not in exclude_set]

        return filtered

    def _entity_to_info(self, entity: PIIEntity, redacted_text: str | None = None) -> EntityInfo:
        """Convert PIIEntity to EntityInfo schema."""
        return EntityInfo(
            text=entity.text,
            label=entity.label,
            confidence=entity.confidence,
            start=entity.start,
            end=entity.end,
            redacted_text=redacted_text,
        )

    def extract_entities(
        self,
        text: str,
        config: RedactionConfig,
    ) -> list[EntityInfo]:
        """Extract PII entities from text without redaction."""
        model_name = config.model or self.active_model_name
        device = self._get_device(config.device.value)

        logger.info(f"Extracting PII with model={model_name}, threshold={config.confidence_threshold}")

        result = extract_pii(
            text,
            model_name=model_name,
            confidence_threshold=config.confidence_threshold,
            use_smart_merging=config.use_smart_merging,
        )

        entities = self._filter_entities(
            result.entities,
            config.entity_types,
            config.exclude_entity_types,
        )

        return [self._entity_to_info(e) for e in entities]

    def _generate_replacement(self, entity: PIIEntity, method: str) -> str:
        """Generate replacement text for an entity based on method."""
        if method == "mask":
            return f"[{entity.label}]"
        elif method == "remove":
            return ""
        elif method == "hash":
            return hashlib.md5(entity.text.encode("utf-8")).hexdigest()[:8]
        elif method == "replace":
             # Fallback for manual replacement if openmed synthetic generation is skipped
             # Since we don't have a synthetic data generator here easily
             return f"[{entity.label}]" 
        else:
             return f"[{entity.label}]"

    def _redact_manual(self, text: str, entities: list[PIIEntity], method: str) -> str:
        """Manually redact text based on entities list."""
        # Sort entities by start position descending to avoid offset issues
        sorted_entities = sorted(entities, key=lambda x: x.start, reverse=True)
        
        # Working with list of characters for mutability
        chars = list(text)

        for entity in sorted_entities:
            # Safety check
            if entity.start < 0 or entity.end > len(text):
                continue
                
            replacement = self._generate_replacement(entity, method)
            
            # Replace slice
            # Note: entity.end is exclusive
            chars[entity.start:entity.end] = list(replacement)

        return "".join(chars)

    def redact_text(
        self,
        text: str,
        config: RedactionConfig,
    ) -> RedactionResult:
        """Redact PII from text using specified method."""
        model_name = config.model or self.active_model_name
        method = config.method.value
        device = self._get_device(config.device.value)

        logger.info(f"Redacting text with model={model_name}, method={method}")

        # Check if we need to filter entities
        filtering_needed = (config.entity_types is not None) or (config.exclude_entity_types is not None)

        if filtering_needed or method != "replace":
            # STRATEGY 1: Extract + Manual Redaction (Preferred for filtering or simple methods)
            # We skip 'replace' here unless filtering is needed, because synthetic replacement is hard to do manually without a generator.
            # If filtering IS needed with 'replace', we fallback to mask/placeholder behavior in _generate_replacement
            # because openmed doesn't support filtered generation apparently.
            
            extraction_result = extract_pii(
                text,
                model_name=model_name,
                confidence_threshold=config.confidence_threshold,
                use_smart_merging=config.use_smart_merging,
            )
            
            all_entities = extraction_result.entities
            filtered_entities = self._filter_entities(
                all_entities,
                config.entity_types,
                config.exclude_entity_types,
            )
            
            redacted_text = self._redact_manual(text, filtered_entities, method)
            
            # Result entities
            final_entities = [self._entity_to_info(e) for e in filtered_entities]
            
            return RedactionResult(
                original_text=text,
                redacted_text=redacted_text,
                entities=final_entities,
                entity_count=len(final_entities),
                mapping=None,
                method=method,
                model=model_name,
                confidence_threshold=config.confidence_threshold,
            )

        else:
            # STRATEGY 2: Use matching openmed deidentify (Best for 'replace' without filters)
            # This path is used when NO filtering is active, so we can trust deidentify to handle everything
            kwargs: dict[str, Any] = {
                "method": method,
                "model_name": model_name,
                "confidence_threshold": config.confidence_threshold,
                "use_smart_merging": config.use_smart_merging,
            }

            if method == "shift_dates" and config.date_shift_days is not None:
                kwargs["date_shift_days"] = config.date_shift_days

            if config.include_mapping:
                kwargs["keep_mapping"] = True

            result = deidentify(text, **kwargs)

            # Get entities from result
            entities_raw = getattr(result, "pii_entities", None) or getattr(result, "entities", [])
            entities = []
            for entity in entities_raw:
                redacted = getattr(entity, "redacted_text", None)
                entities.append(self._entity_to_info(entity, redacted))

            mapping = None
            if config.include_mapping:
                raw_map = getattr(result, "mapping", None)
                if raw_map:
                    mapping = dict(raw_map)

            return RedactionResult(
                original_text=text,
                redacted_text=result.deidentified_text,
                entities=entities,
                entity_count=len(entities),
                mapping=mapping,
                method=method,
                model=model_name,
                confidence_threshold=config.confidence_threshold,
            )

    def redact_batch(
        self,
        texts: list[str],
        ids: list[str] | None,
        config: RedactionConfig,
    ) -> BatchRedactionResult:
        """Redact multiple texts in batch."""
        # Parallel processing could be added here
        start_time = time.time()

        if ids is None:
            ids = [f"item_{i}" for i in range(len(texts))]

        results: list[RedactionResult] = []
        failed = 0
        total_entities = 0

        for i, text in enumerate(texts):
            try:
                result = self.redact_text(text, config)
                results.append(result)
                total_entities += result.entity_count
            except Exception as e:
                logger.error(f"Failed to process item {ids[i]}: {e}")
                failed += 1
                results.append(
                    RedactionResult(
                        original_text=text,
                        redacted_text=text,
                        entities=[],
                        entity_count=0,
                        mapping=None,
                        method=config.method.value,
                        model=config.model,
                        confidence_threshold=config.confidence_threshold,
                    )
                )

        processing_time = time.time() - start_time

        return BatchRedactionResult(
            results=results,
            total_items=len(texts),
            successful_items=len(texts) - failed,
            failed_items=failed,
            total_entities=total_entities,
            processing_time_seconds=round(processing_time, 3),
        )


# Singleton instance
@lru_cache
def get_redaction_service() -> RedactionService:
    """Get cached redaction service instance."""
    return RedactionService()
