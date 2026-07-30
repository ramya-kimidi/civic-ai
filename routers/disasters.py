from fastapi import APIRouter, Depends, Request, Form, Body, HTTPException, status
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from database import get_db
import models
from auth_utils import get_current_user

router = APIRouter()

@router.post("/api/disasters")
def create_disaster(
    request: Request,
    disaster_type: str = Form(...),
    title: str = Form(...),
    area: str = Form(...),
    description: str = Form(...),
    severity: str = Form("Medium"),
    latitude: float = Form(...),
    longitude: float = Form(...),
    db: Session = Depends(get_db)
):
    user = get_current_user(request, db)
    
    new_disaster = models.Disaster(
        disaster_type=disaster_type,
        title=title.strip(),
        area=area.strip(),
        description=description.strip(),
        severity=severity,
        latitude=latitude,
        longitude=longitude,
        is_active=True,
        created_by_id=user.id if user else None
    )
    db.add(new_disaster)
    db.commit()
    db.refresh(new_disaster)

    request.session["flash_success"] = f"Disaster warning '{title}' published successfully!"
    return RedirectResponse(url="/city-admin/dashboard", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/api/disasters")
def list_disasters(db: Session = Depends(get_db)):
    disasters = db.query(models.Disaster).order_by(models.Disaster.created_at.desc()).all()
    res = []
    for d in disasters:
        res.append({
            "id": d.id,
            "disaster_type": d.disaster_type,
            "title": d.title,
            "area": d.area,
            "description": d.description,
            "severity": d.severity,
            "latitude": d.latitude,
            "longitude": d.longitude,
            "is_active": d.is_active,
            "created_at": d.created_at.strftime("%I:%M %p, %b %d")
        })
    return res

@router.post("/api/disasters/{disaster_id}/toggle")
def toggle_disaster(
    disaster_id: int,
    db: Session = Depends(get_db)
):
    disaster = db.query(models.Disaster).filter(models.Disaster.id == disaster_id).first()
    if not disaster:
        raise HTTPException(status_code=404, detail="Disaster not found")

    disaster.is_active = not disaster.is_active
    db.commit()
    return {"status": "success", "is_active": disaster.is_active}
