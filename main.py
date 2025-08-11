"""
Main FastAPI application for the API Conference AI Agent.
"""

import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from app.config.logger import Logger
from app.config.settings import settings
from app.api.v1.agents_router import router as agents_router
from app.api.v1.literature_router import router as literature_router

# Setup logging
Logger.setup_root_logger()
logger = Logger.get_logger(__name__)

# Global startup time
startup_time = time.time()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting API Conference AI Agent...")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Model: {settings.google_model_name}")
    logger.info(f"Venue: {settings.conference_venue_name}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down API Conference AI Agent...")

# Create FastAPI app
app = FastAPI(
    title="API Conference AI Agent",
    description="AI Assistant for the API Conference community in Nigeria",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(agents_router, prefix="/api/v1/agents", tags=["agents"])
app.include_router(literature_router, prefix="/api/v1/literature", tags=["literature"])

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to API Conference AI Agent! 🎤",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/api/v1/agents/health",
        "support": settings.support_phone
    }

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "message": f"Please contact {settings.support_phone} for assistance.",
            "support_contact": settings.support_phone
        }
    )

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time header to responses."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

if __name__ == "__main__":
    logger.info("Starting server...")
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    ) 