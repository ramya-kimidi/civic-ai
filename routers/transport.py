from fastapi import APIRouter, Depends, Request, Form, Body, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from database import get_db
import models
from auth_utils import get_current_user

router = APIRouter()

@router.post("/api/emergency-request")
async def create_emergency_request(
    request: Request,
    payload: dict = Body(...),
    db: Session = Depends(get_db)
):
    user = get_current_user(request, db)
    req_type = payload.get("request_type")
    lat = payload.get("latitude")
    lng = payload.get("longitude")
    desc = payload.get("description", "")

    if not req_type or lat is None or lng is None:
        raise HTTPException(status_code=400, detail="Missing required parameters")

    new_req = models.EmergencyRequest(
        user_id=user.id if user else None,
        request_type=req_type,
        description=desc,
        latitude=float(lat),
        longitude=float(lng),
        status="Pending"
    )
    db.add(new_req)
    db.commit()
    db.refresh(new_req)

    return JSONResponse({
        "status": "success",
        "message": f"{req_type} request dispatched successfully!",
        "request_id": new_req.id,
        "current_status": new_req.status
    })

@router.get("/api/emergency-requests")
def get_emergency_requests(db: Session = Depends(get_db)):
    requests = db.query(models.EmergencyRequest).order_by(models.EmergencyRequest.created_at.desc()).all()
    res = []
    for r in requests:
        res.append({
            "id": r.id,
            "user_name": r.user.full_name if r.user else "Anonymous Citizen",
            "user_phone": r.user.phone if r.user else "N/A",
            "request_type": r.request_type,
            "description": r.description,
            "latitude": r.latitude,
            "longitude": r.longitude,
            "status": r.status,
            "created_at": r.created_at.strftime("%I:%M %p, %b %d")
        })
    return res

@router.post("/api/emergency-requests/{req_id}/status")
async def update_transport_status(
    req_id: int,
    payload: dict = Body(...),
    db: Session = Depends(get_db)
):
    req_item = db.query(models.EmergencyRequest).filter(models.EmergencyRequest.id == req_id).first()
    if not req_item:
        raise HTTPException(status_code=404, detail="Request not found")

    new_status = payload.get("status")
    if new_status in ["Pending", "Accepted", "On The Way", "Resolved"]:
        req_item.status = new_status
        db.commit()
        return {"status": "success", "message": f"Transport status updated to {new_status}"}

    raise HTTPException(status_code=400, detail="Invalid status value")
