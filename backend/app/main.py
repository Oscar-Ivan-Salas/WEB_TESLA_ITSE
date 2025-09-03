"""
Main FastAPI application for the Tesla CRM API.
"""
import os
import logging
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import database and models to ensure tables are created
from .database import engine, Base
from .models import *  # noqa

# Import routers
from .api.v1 import router as api_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/token")

# Create FastAPI app
app = FastAPI(
    title="Tesla CRM API",
    description="API for Tesla CRM application",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router)

# Trusted Hosts middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=os.getenv("ALLOWED_HOSTS", "*").split("|"),
)

# Session middleware
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY", "your-secret-key-here"),
    session_cookie="tesla_session",
)

# Include API routers
app.include_router(api_router, prefix="/api/v1")

# Health check endpoint
@app.get("/healthz", tags=["health"])
async def health_check():
    """Health check endpoint for load balancers and monitoring."""
    return {
        "status": "ok",
        "version": "0.1.0",
        "environment": os.getenv("ENV", "development"),
    }

# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """Root endpoint that provides API information."""
    return {
        "name": "Tesla CRM API",
        "version": "0.1.0",
        "docs": "/api/docs",
        "redoc": "/api/redoc"
    }

# Add exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions with a JSON response."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

# Add startup event to initialize data
@app.on_event("startup")
def startup_event():
    """Initialize data when the application starts."""
    from .init_db import create_initial_data
    
    logger.info("Starting up Tesla CRM API...")
    
    try:
        # Create initial data if needed
        create_initial_data()
        logger.info("Initial data check completed.")
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise

# Add shutdown event
@app.on_event("shutdown")
def shutdown_event():
    """Clean up when the application shuts down."""
    logger.info("Shutting down Tesla CRM API...")
