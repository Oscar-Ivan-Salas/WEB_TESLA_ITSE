"""
Database configuration and session management for the Tesla CRM application.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database URL from environment variables or default to SQLite
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./tesla.db")

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all models
Base = declarative_base()

def get_db():
    """
    Dependency to get DB session.
    Use this in your FastAPI path operations to get a database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
