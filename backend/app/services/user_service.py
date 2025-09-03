"""
User service for handling user-related business logic.
"""
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models import User, ActivityLog
from app.schemas.user import UserCreate, UserUpdate, UserRole, UserStatus
from app.core.security import get_password_hash, verify_password

class UserService:
    """Service class for user-related operations."""
    
    @staticmethod
    async def create_user(
        db: Session, 
        user_in: UserCreate
    ) -> User:
        """Create a new user."""
        # Check if user with this email already exists
        existing_user = await UserService.get_user_by_email(db, email=user_in.email)
        if existing_user:
            raise ValueError("Email already registered")
        
        # Hash the password
        hashed_password = get_password_hash(user_in.password)
        
        # Create user object
        db_user = User(
            email=user_in.email,
            hashed_password=hashed_password,
            first_name=user_in.first_name,
            last_name=user_in.last_name,
            role=user_in.role or UserRole.USER,
            status=UserStatus.ACTIVE,
            is_superuser=user_in.is_superuser or False,
        )
        
        # Add optional fields if provided
        if user_in.phone:
            db_user.phone = user_in.phone
        
        if user_in.position:
            db_user.position = user_in.position
        
        if user_in.department:
            db_user.department = user_in.department
        
        # Save to database
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        # Log the user creation
        await ActivityLog.log_activity(
            db,
            action="user.created",
            entity_type="user",
            entity_id=db_user.id,
            user_id=db_user.id,
            details={"role": db_user.role, "status": db_user.status}
        )
        
        return db_user
    
    @staticmethod
    async def get_user(
        db: Session, 
        user_id: int
    ) -> Optional[User]:
        """Get a user by ID."""
        return db.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    async def get_user_by_email(
        db: Session, 
        email: str
    ) -> Optional[User]:
        """Get a user by email."""
        return db.query(User).filter(User.email == email).first()
    
    @staticmethod
    async def get_users(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        role: Optional[UserRole] = None,
        status: Optional[UserStatus] = None,
        search: Optional[str] = None,
    ) -> List[User]:
        """
        Get a list of users with optional filtering.
        
        Args:
            db: Database session
            skip: Number of records to skip for pagination
            limit: Maximum number of records to return
            role: Filter by user role
            status: Filter by user status
            search: Search term to filter by name or email
            
        Returns:
            List of User objects
        """
        query = db.query(User)
        
        # Apply filters
        if role:
            query = query.filter(User.role == role)
        
        if status:
            query = query.filter(User.status == status)
        
        # Apply search
        if search:
            search_filter = or_(
                User.first_name.ilike(f"%{search}%"),
                User.last_name.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)
        
        # Apply pagination
        return query.offset(skip).limit(limit).all()
    
    @staticmethod
    async def update_user(
        db: Session,
        user_id: int,
        user_in: UserUpdate,
        current_user: Optional[User] = None,
    ) -> Optional[User]:
        """
        Update a user's information.
        
        Args:
            db: Database session
            user_id: ID of the user to update
            user_in: User data to update
            current_user: The currently authenticated user (for permission checks)
            
        Returns:
            Updated User object if successful, None if user not found
        """
        db_user = await UserService.get_user(db, user_id)
        if not db_user:
            return None
        
        # Check permissions
        if current_user and not current_user.is_superuser and current_user.id != user_id:
            raise PermissionError("Not authorized to update this user")
        
        # Track changes for activity log
        changes = {}
        update_data = user_in.dict(exclude_unset=True)
        
        # Update user fields
        for field, value in update_data.items():
            # Skip password updates (handled separately)
            if field == 'password':
                continue
                
            old_value = getattr(db_user, field, None)
            if old_value != value:
                changes[field] = {"old": old_value, "new": value}
                setattr(db_user, field, value)
        
        # Only update if there are changes
        if changes:
            db_user.updated_at = datetime.utcnow()
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            
            # Log the update
            await ActivityLog.log_activity(
                db,
                action="user.updated",
                entity_type="user",
                entity_id=db_user.id,
                user_id=current_user.id if current_user else None,
                details={"changes": changes}
            )
        
        return db_user
    
    @staticmethod
    async def update_password(
        db: Session,
        user_id: int,
        new_password: str,
        current_user: Optional[User] = None,
    ) -> bool:
        """
        Update a user's password.
        
        Args:
            db: Database session
            user_id: ID of the user to update
            new_password: New password to set
            current_user: The currently authenticated user (for permission checks)
            
        Returns:
            True if successful, False if user not found
        """
        db_user = await UserService.get_user(db, user_id)
        if not db_user:
            return False
        
        # Check permissions
        if current_user and not current_user.is_superuser and current_user.id != user_id:
            raise PermissionError("Not authorized to update this user's password")
        
        # Update password
        db_user.hashed_password = get_password_hash(new_password)
        db_user.updated_at = datetime.utcnow()
        
        db.add(db_user)
        db.commit()
        
        # Log the password change
        await ActivityLog.log_activity(
            db,
            action="user.password_updated",
            entity_type="user",
            entity_id=db_user.id,
            user_id=current_user.id if current_user else None,
            details={"password_changed": True}
        )
        
        return True
    
    @staticmethod
    async def delete_user(
        db: Session,
        user_id: int,
        current_user: Optional[User] = None,
    ) -> bool:
        """
        Delete a user.
        
        In most cases, you'll want to deactivate users instead of deleting them
        to maintain referential integrity. This method is provided for completeness.
        
        Args:
            db: Database session
            user_id: ID of the user to delete
            current_user: The currently authenticated user (for permission checks)
            
        Returns:
            True if successful, False if user not found
        """
        db_user = await UserService.get_user(db, user_id)
        if not db_user:
            return False
        
        # Check permissions
        if current_user and not current_user.is_superuser and current_user.id != user_id:
            raise PermissionError("Not authorized to delete this user")
        
        # Prevent deleting your own account if you're not a superuser
        if current_user and current_user.id == user_id and not current_user.is_superuser:
            raise PermissionError("You cannot delete your own account")
        
        # Log the deletion
        await ActivityLog.log_activity(
            db,
            action="user.deleted",
            entity_type="user",
            entity_id=db_user.id,
            user_id=current_user.id if current_user else None,
            details={
                "user_data": {
                    "email": db_user.email,
                    "role": db_user.role,
                    "status": db_user.status
                }
            }
        )
        
        # Delete the user
        db.delete(db_user)
        db.commit()
        
        return True
    
    @staticmethod
    async def deactivate_user(
        db: Session,
        user_id: int,
        current_user: Optional[User] = None,
    ) -> Optional[User]:
        """
        Deactivate a user account.
        
        This is the preferred way to remove a user's access to the system
        while maintaining their data for historical purposes.
        
        Args:
            db: Database session
            user_id: ID of the user to deactivate
            current_user: The currently authenticated user (for permission checks)
            
        Returns:
            Updated User object if successful, None if user not found
        """
        db_user = await UserService.get_user(db, user_id)
        if not db_user:
            return None
        
        # Check permissions
        if current_user and not current_user.is_superuser and current_user.id != user_id:
            raise PermissionError("Not authorized to deactivate this user")
        
        # Prevent deactivating your own account if you're not a superuser
        if current_user and current_user.id == user_id and not current_user.is_superuser:
            raise PermissionError("You cannot deactivate your own account")
        
        # Only update if not already inactive
        if db_user.status != UserStatus.INACTIVE:
            old_status = db_user.status
            db_user.status = UserStatus.INACTIVE
            db_user.updated_at = datetime.utcnow()
            
            db.add(db_user)
            db.commit()
            
            # Log the deactivation
            await ActivityLog.log_activity(
                db,
                action="user.deactivated",
                entity_type="user",
                entity_id=db_user.id,
                user_id=current_user.id if current_user else None,
                details={"old_status": old_status, "new_status": UserStatus.INACTIVE}
            )
        
        return db_user
    
    @staticmethod
    async def activate_user(
        db: Session,
        user_id: int,
        current_user: Optional[User] = None,
    ) -> Optional[User]:
        """
        Activate a previously deactivated user account.
        
        Args:
            db: Database session
            user_id: ID of the user to activate
            current_user: The currently authenticated user (for permission checks)
            
        Returns:
            Updated User object if successful, None if user not found
        """
        db_user = await UserService.get_user(db, user_id)
        if not db_user:
            return None
        
        # Check permissions
        if current_user and not current_user.is_superuser and current_user.id != user_id:
            raise PermissionError("Not authorized to activate this user")
        
        # Only update if currently inactive
        if db_user.status == UserStatus.INACTIVE:
            db_user.status = UserStatus.ACTIVE
            db_user.updated_at = datetime.utcnow()
            
            db.add(db_user)
            db.commit()
            
            # Log the activation
            await ActivityLog.log_activity(
                db,
                action="user.activated",
                entity_type="user",
                entity_id=db_user.id,
                user_id=current_user.id if current_user else None,
                details={"old_status": UserStatus.INACTIVE, "new_status": UserStatus.ACTIVE}
            )
        
        return db_user
    
    @staticmethod
    async def authenticate_user(
        db: Session,
        email: str,
        password: str
    ) -> Optional[User]:
        """
        Authenticate a user with email and password.
        
        Args:
            db: Database session
            email: User's email
            password: Plain text password
            
        Returns:
            User object if authentication is successful, None otherwise
        """
        user = await UserService.get_user_by_email(db, email=email)
        if not user:
            # User not found
            return None
        
        if not verify_password(password, user.hashed_password):
            # Invalid password
            return None
        
        # Check if user is active
        if user.status != UserStatus.ACTIVE:
            return None
        
        # Update last login timestamp
        user.last_login = datetime.utcnow()
        db.add(user)
        db.commit()
        
        # Log the login
        await ActivityLog.log_activity(
            db,
            action="user.logged_in",
            entity_type="user",
            entity_id=user.id,
            user_id=user.id,
            details={"login_time": user.last_login.isoformat()}
        )
        
        return user
    
    @staticmethod
    async def get_user_stats(
        db: Session,
        user_id: int
    ) -> Dict[str, Any]:
        """
        Get statistics for a specific user.
        
        This could include metrics like number of leads, conversions, etc.
        """
        # This is a placeholder implementation
        # In a real application, you would query the database for actual statistics
        
        return {
            "user_id": user_id,
            "leads_count": 0,  # Would be actual counts
            "conversions_count": 0,
            "activities_count": 0,
            "response_time_avg": 0.0,
            "conversion_rate": 0.0,
        }
    
    @staticmethod
    async def get_user_activities(
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 50,
    ) -> List[ActivityLog]:
        """
        Get activity logs for a specific user.
        
        Args:
            db: Database session
            user_id: ID of the user
            skip: Number of records to skip for pagination
            limit: Maximum number of records to return
            
        Returns:
            List of ActivityLog objects
        """
        return (
            db.query(ActivityLog)
            .filter(ActivityLog.user_id == user_id)
            .order_by(ActivityLog.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

# Create a singleton instance
user_service = UserService()
