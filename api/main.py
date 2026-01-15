"""PII Redaction Tool API - Production-grade PII redaction service."""

import logging
import sys
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Add Core to path
core_path = Path(__file__).resolve().parents[1] / "core"
sys.path.append(str(core_path))

from redac_core.config import get_settings
from redac_core.services import get_redaction_service, get_document_handler

# Import Routers (Update imports inside routers separately)
from routers import redact, documents, config as config_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("🚀 Starting PII Redaction Tool API...")
    logger.info(f"   Default model: {settings.default_model}")
    logger.info(f"   Device: {settings.device}")
    logger.info(f"   Max file size: {settings.max_file_size_mb}MB")

    # Pre-warm the model (optional, can be disabled for faster startup)
    if not settings.debug:
        try:
            get_redaction_service()
            logger.info("   Model pre-warming completed ✓")
        except Exception as e:
            logger.warning(f"   Model pre-warming failed: {e}")

    yield

    # Shutdown
    logger.info("🛑 Shutting down PII Redaction Tool API...")
    get_document_handler().cleanup()


# Create FastAPI app
app = FastAPI(
    title="PII Redaction Tool API",
    description="Production-grade PII redaction service powered by OpenMed",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle validation errors."""
    return JSONResponse(
        status_code=400,
        content={"error": "validation_error", "message": str(exc)},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors."""
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "internal_error", "message": "An unexpected error occurred"},
    )


# Include routers
app.include_router(redact.router, prefix="/api/v1", tags=["Redaction"])
app.include_router(documents.router, prefix="/api/v1", tags=["Documents"])
app.include_router(config_router.router, prefix="/api/v1", tags=["Configuration"])


# Health endpoints
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "default_model": settings.default_model,
    }


@app.get("/ready", tags=["Health"])
async def readiness_check():
    """Readiness check - verifies model is loaded."""
    try:
        get_redaction_service()
        return {
            "status": "ready",
            "model_loaded": True,
            "default_model": settings.default_model,
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "model_loaded": False,
                "error": str(e),
            },
        )


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "PII Redaction Tool API",
        "description": "Production-grade PII redaction service",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "api": "/api/v1",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level,
    )
