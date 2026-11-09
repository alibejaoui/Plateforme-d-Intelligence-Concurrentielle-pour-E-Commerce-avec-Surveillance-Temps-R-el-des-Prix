"""
Main FastAPI application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.settings import settings
from app.core.logging import setup_logging
from app.core.database import init_db
from app.api.router import api_router
from app.core.database import SessionLocal
from app.services.demo_bootstrap_service import ensure_demo_users


# Setup logging
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown"""
    # Startup
    import logging
    logger = logging.getLogger("app")
    try:
        logger.info("Initializing database...")
        init_db()
        # Bootstrap demo users for presentation reliability.
        db = None
        try:
            db = SessionLocal()
            ensure_demo_users(db)
        finally:
            if db is not None:
                db.close()
        logger.info("Database initialization completed")
    except Exception as e:
        logger.warning(f"Database initialization failed (will retry on first request): {e}")
        # Don't crash the app if DB is not ready yet
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    # Add cleanup code here if needed


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Plateforme d'Intelligence Concurrentielle pour E-Commerce avec Surveillance Temps Réel des Prix",
    lifespan=lifespan
)

# CORS middleware – explicitly allow Authorization (required when credentials=True in some browsers)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin", "X-Requested-With"],
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Plateforme d'Intelligence Concurrentielle API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/api/v1/monitoring/health"
    }


@app.get("/health")
async def health():
    """Simple health check"""
    return {"status": "ok"}

