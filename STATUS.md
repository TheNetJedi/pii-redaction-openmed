# Project Status Report

## 1. Architectural Refactor
Successfully migrated to a modular architecture:
- **Core Library (`redac_core`)**: All business logic (PII detection, PDF/DOCX handling, config) is now central.
- **API**: Now a thin wrapper around `redac_core`, reducing code duplication.
- **CLI**: Now has full feature parity with API (PDF support) by using `redac_core`.

## 2. Critical Fixes
- **Selective Redaction**: Fixed a crash where sending `entity_types` (filtering) caused a `TypeError`. Implemented robust manual redaction logic to fallback when filtering is needed.
- **Frontend Regression**: Fixed `ReferenceError: Eraser is not defined` by restoring missing icon imports.
- **Docker Build**: Fixed `api` Dockerfile to correctly include the new `core` library using a multi-stage root-context build.

## 3. UI/UX Improvements
- **Visuals**: Enhanced PII entity list with specific icons (e.g., Credit Card icon for financial data).
- **Documentation**: Updated `README.md` with architecture diagrams, local dev instructions, and proper credits to OpenMed.

## 4. Next Steps
- **Testing**: Manual testing of the new Docker build is recommended (`docker-compose up --build`).
- **Optimization**: The `Manual Redaction` path works well, but `replace` (synthetic data) is currently limited to masking when filtering is active. Future work could integrate a dedicated synthetic data generator.
