from fastapi import APIRouter, Depends, Request, Form, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from database import get_db
import models
from auth_utils import hash_password, verify_password, get_current_user, set_active_user_id, clear_active_user_id

router = APIRouter()

@router.post("/login")
def login(
    request: Request,
    email_or_username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(
        (models.User.email == email_or_username) | (models.User.username == email_or_username)
    ).first()

    if not user or not verify_password(password, user.hashed_password):
        request.session["flash_error"] = "Invalid username/email or password."
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    # Set session and active memory
    request.session["user_id"] = user.id
    request.session["user_name"] = user.full_name
    request.session["user_role"] = user.role
    request.session["flash_success"] = f"Welcome back, {user.full_name}!"
    set_active_user_id(user.id)

    # Target URL based on role
    target_url = "/user/dashboard"
    if user.role == "city_admin":
        target_url = "/city-admin/dashboard"
    elif user.role == "emergency_admin":
        target_url = "/emergency-admin/dashboard"

    response = RedirectResponse(url=target_url, status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie("smartcivic_user_id", str(user.id), max_age=86400*30, path="/", samesite="lax")
    return response

@router.post("/register")
def register(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    full_name: str = Form(...),
    phone: str = Form(...),
    password: str = Form(...),
    role: str = Form("citizen"),
    db: Session = Depends(get_db)
):
    # Check existing user
    existing = db.query(models.User).filter(
        (models.User.email == email) | (models.User.username == username)
    ).first()

    if existing:
        request.session["flash_error"] = "Username or email already exists."
        return RedirectResponse(url="/register", status_code=status.HTTP_303_SEE_OTHER)

    # Sanitize role
    if role not in ["citizen", "city_admin", "emergency_admin"]:
        role = "citizen"

    new_user = models.User(
        username=username.strip(),
        email=email.strip().lower(),
        full_name=full_name.strip(),
        phone=phone.strip(),
        hashed_password=hash_password(password),
        role=role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Auto log in and set active memory
    request.session["user_id"] = new_user.id
    request.session["user_name"] = new_user.full_name
    request.session["user_role"] = new_user.role
    request.session["flash_success"] = f"Account created successfully for {new_user.full_name}! Welcome to SmartCivic."
    set_active_user_id(new_user.id)

    target_url = "/user/dashboard"
    if new_user.role == "city_admin":
        target_url = "/city-admin/dashboard"
    elif new_user.role == "emergency_admin":
        target_url = "/emergency-admin/dashboard"

    response = RedirectResponse(url=target_url, status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie("smartcivic_user_id", str(new_user.id), max_age=86400*30, path="/", samesite="lax")
    return response

@router.post("/profile/update")
def update_profile(
    request: Request,
    full_name: str = Form(...),
    phone: str = Form(""),
    db: Session = Depends(get_db)
):
    user = get_current_user(request, db)
    if not user:
        request.session["flash_error"] = "Please log in first."
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    user.full_name = full_name.strip()
    user.phone = phone.strip()
    db.commit()

    request.session["user_name"] = user.full_name
    request.session["flash_success"] = "Profile updated successfully!"
    return RedirectResponse(url="/profile", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/profile/switch-role")
def switch_role(
    request: Request,
    role: str = Form(...),
    db: Session = Depends(get_db)
):
    user = get_current_user(request, db)
    if not user:
        request.session["flash_error"] = "Please log in first."
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    if role in ["citizen", "city_admin", "emergency_admin"]:
        user.role = role
        db.commit()
        request.session["user_role"] = role
        request.session["flash_success"] = f"Switched role to {role.replace('_', ' ').title()}!"

    return RedirectResponse(url="/profile", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/api/sync-session")
def sync_session(request: Request, db: Session = Depends(get_db)):
    user_id = request.query_params.get("user_id") or request.cookies.get("smartcivic_user_id")
    if user_id and str(user_id).isdigit():
        uid = int(user_id)
        user = db.query(models.User).filter(models.User.id == uid).first()
        if user:
            request.session["user_id"] = user.id
            request.session["user_name"] = user.full_name
            request.session["user_role"] = user.role
            set_active_user_id(user.id)
            return {"status": "ok", "user": {"id": user.id, "name": user.full_name, "role": user.role}}
    return {"status": "guest"}

@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    clear_active_user_id()
    response = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("smartcivic_user_id", path="/")
    return response
