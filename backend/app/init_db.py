"""
Database initialization script for the Tesla CRM application.
"""
import logging
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError

from .database import Base, engine
from .models import User, UserRole, Lead, Conversation, Message, ActivityLog

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_db() -> None:
    """Initialize the database by creating all tables and adding initial data."""
    try:
        # Create all tables
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully.")
        
    except SQLAlchemyError as e:
        logger.error(f"Error initializing database: {e}")
        raise

def create_initial_data() -> None:
    """Create initial data for the application."""
    from sqlalchemy.orm import sessionmaker
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Check if we already have users
        if db.query(User).first() is None:
            logger.info("Creating initial admin user...")
            
            # Create admin user
            admin = User(
                email="admin@teslacrm.com",
                first_name="Admin",
                last_name="User",
                role=UserRole.ADMIN,
                status="active"
            )
            admin.set_password("admin123")
            
            db.add(admin)
            db.commit()
            logger.info("Initial admin user created successfully.")
        
        # Add other initial data as needed
        
    except SQLAlchemyError as e:
        logger.error(f"Error creating initial data: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    # Initialize the database when this script is run directly
    init_db()
    create_initial_data()
