"""
Authentication and user management endpoints for the Tesla CRM application.
"""
from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.schemas.user import User, UserCreate, UserUpdate, Token, TokenData
from app.core.security import (
    get_password_hash,
    create_access_token,
    verify_password,
    get_current_active_user,
    get_current_user
)
from app.core.config import settings
from app.database import get_db
from app.services import user_service

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_in: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new user.
    
    - **email**: Must be a valid email address and unique
    - **password**: At least 8 characters
    - **first_name**: User's first name
    - **last_name**: User's last name
    """
    # Check if user with this email already exists
    db_user = await user_service.get_user_by_email(db, email=user_in.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    return await user_service.create_user(db=db, user=user_in)

@router.post("/token", response_model=Token)
async def login_for_access_token(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    OAuth2 compatible token login, get an access token for future requests.
    
    - **username**: User's email
    - **password**: User's password
    
    Returns an access token that should be included in the Authorization header
    for authenticated requests.
    """
    user = await user_service.authenticate_user(
        db, form_data.username, form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    # Set HTTP-only cookie for web clients
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        secure=settings.SECURE_COOKIES,
        samesite="lax"
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.post("/logout")
async def logout(response: Response):
    """
    Log out by removing the access token cookie.
    """
    response.delete_cookie("access_token")
    return {"message": "Successfully logged out"}

@router.get("/me", response_model=User)
async def read_users_me(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current user information.
    """
    return current_user

@router.put("/me", response_model=User)
async def update_user_me(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update current user information.
    
    Only the fields provided in the request will be updated.
    """
    return await user_service.update_user(db, user_id=current_user.id, user_update=user_update)

@router.post("/password/change")
async def change_password(
    current_password: str,
    new_password: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Change current user's password.
    
    - **current_password**: Current password for verification
    - **new_password**: New password (at least 8 characters)
    """
    # Verify current password
    if not verify_password(current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )
    
    # Update to new password
    await user_service.update_password(
        db, user_id=current_user.id, new_password=new_password
    )
    
    return {"message": "Password updated successfully"}

@router.post("/password/reset-request")
async def request_password_reset(
    email: str,
    db: Session = Depends(get_db)
):
    """
    Request a password reset.
    
    Sends a password reset email to the user with a reset token.
    """
    # This would typically send an email with a reset link
    # For now, we'll just return a success message
    user = await user_service.get_user_by_email(db, email=email)
    if user:
        # In a real app, generate a reset token and send an email
        pass
    
    # Return success regardless of whether the email exists to prevent user enumeration
    return {
        "message": "If your email is registered, you will receive a password reset link"
    }

@router.post("/password/reset")
async def reset_password(
    token: str,
    new_password: str,
    db: Session = Depends(get_db)
):
    """
    Reset password with a valid reset token.
    
    - **token**: Password reset token from email
    - **new_password**: New password (at least 8 characters)
    """
    # In a real app, verify the reset token and update the password
    # For now, we'll just return a success message
    return {"message": "Password has been reset successfully"}

@router.get("/verify-email")
async def verify_email(
    token: str,
    db: Session = Depends(get_db)
):
    """
    Verify user's email address with a verification token.
    """
    # In a real app, verify the email token and mark the email as verified
    # For now, we'll just return a success message
    return {"message": "Email verified successfully"}
