import hashlib
import os
from typing import Optional
from fastapi import Request, HTTPException, status
from sqlalchemy.orm import Session
import models

# Global fallback for single-user iframe session resilience
_ACTIVE_USER_ID: Optional[int] = None

def set_active_user_id(user_id: int):
    global _ACTIVE_USER_ID
    _ACTIVE_USER_ID = user_id

def clear_active_user_id():
    global _ACTIVE_USER_ID
    _ACTIVE_USER_ID = None

# Password hashing using sha256 + salt
def hash_password(password: str) -> str:
    salt = "smartcivic_salt_2026"
    return hashlib.sha256((password + salt).encode('utf-8')).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hash_password(plain_password) == hashed_password

# Get logged in user from session cookie, fallback cookie, query param, or active user memory
def get_current_user(request: Request, db: Session) -> Optional[models.User]:
    global _ACTIVE_USER_ID
    user_id = request.session.get("user_id")
    
    # Fallback 1: Direct Cookie check
    if not user_id:
        user_id = request.cookies.get("smartcivic_user_id")
    
    # Fallback 2: URL Query parameter (for iframe navigation safety)
    if not user_id:
        user_id_param = request.query_params.get("user_id")
        if user_id_param and str(user_id_param).isdigit():
            user_id = user_id_param

    # Fallback 3: Active memory session
    if not user_id and _ACTIVE_USER_ID is not None:
        user_id = _ACTIVE_USER_ID

    if not user_id:
        return None

    try:
        uid = int(user_id)
        user = db.query(models.User).filter(models.User.id == uid).first()
        if user:
            # Sync back to session and active memory
            request.session["user_id"] = user.id
            request.session["user_name"] = user.full_name
            request.session["user_role"] = user.role
            _ACTIVE_USER_ID = user.id
        return user
    except Exception:
        return None

def require_user(request: Request, db: Session) -> models.User:
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    return user

def require_role(allowed_roles: list[str]):
    def role_checker(request: Request, db: Session):
        user = require_user(request, db)
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied for this user role"
            )
        return user
    return role_checker
