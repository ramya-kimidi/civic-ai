from fastapi import APIRouter, Depends, Request, Form, Body, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from database import get_db
import models
from auth_utils import get_current_user

router = APIRouter()

@router.post("/api/sos")
async def create_sos_alert(
    request: Request,
    payload: dict = Body(...),
    db: Session = Depends(get_db)
):
    user = get_current_user(request, db)
    lat = payload.get("latitude")
    lng = payload.get("longitude")
    address = payload.get("address", "Captured GPS Location")

    if lat is None or lng is None:
        raise HTTPException(status_code=400, detail="Latitude and Longitude are required")

    alert = models.Alert(
        user_id=user.id if user else None,
        alert_type="SOS",
        latitude=float(lat),
        longitude=float(lng),
        address=address,
        status="Pending",
        notes=payload.get("notes", "Emergency SOS triggered by citizen")
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)

    return JSONResponse({
        "status": "success",
        "message": "Emergency SOS Alert dispatched successfully!",
        "alert_id": alert.id,
        "created_at": alert.created_at.strftime("%Y-%m-%d %H:%M:%S")
    })

@router.post("/api/accident-alert")
async def create_accident_alert(
    request: Request,
    payload: dict = Body(...),
    db: Session = Depends(get_db)
):
    user = get_current_user(request, db)
    lat = payload.get("latitude")
    lng = payload.get("longitude")
    sensor_data = payload.get("sensor_data", "Sudden motion / impact acceleration detected")

    if lat is None or lng is None:
        raise HTTPException(status_code=400, detail="GPS coordinates required")

    alert = models.Alert(
        user_id=user.id if user else None,
        alert_type="Accident",
        latitude=float(lat),
        longitude=float(lng),
        address=payload.get("address", "Crash Detection GPS Point"),
        status="Pending",
        notes=f"Possible Vehicle Accident Detected ({sensor_data})"
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)

    return JSONResponse({
        "status": "success",
        "message": "Accident alert registered and dispatched to emergency teams!",
        "alert_id": alert.id
    })

@router.get("/api/alerts")
def get_alerts(db: Session = Depends(get_db)):
    alerts = db.query(models.Alert).order_by(models.Alert.created_at.desc()).all()
    res = []
    for a in alerts:
        res.append({
            "id": a.id,
            "alert_type": a.alert_type,
            "user_name": a.user.full_name if a.user else "Anonymous Citizen",
            "user_phone": a.user.phone if a.user else "N/A",
            "latitude": a.latitude,
            "longitude": a.longitude,
            "address": a.address,
            "status": a.status,
            "notes": a.notes,
            "created_at": a.created_at.strftime("%I:%M %p, %b %d")
        })
    return res

@router.post("/api/alerts/{alert_id}/status")
async def update_alert_status(
    alert_id: int,
    payload: dict = Body(...),
    db: Session = Depends(get_db)
):
    alert = db.query(models.Alert).filter(models.Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    new_status = payload.get("status")
    if new_status in ["Pending", "Accepted", "Responding", "Resolved"]:
        alert.status = new_status
        db.commit()
        return {"status": "success", "message": f"Alert status updated to {new_status}"}
    
    raise HTTPException(status_code=400, detail="Invalid status value")
