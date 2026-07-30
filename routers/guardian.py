import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, Request, Body, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from database import get_db
import models
from auth_utils import get_current_user

router = APIRouter()

@router.post("/api/journey/start")
async def start_journey(
    request: Request,
    payload: dict = Body(...),
    db: Session = Depends(get_db)
):
    user = get_current_user(request, db)
    
    traveller_name = payload.get("traveller_name") or (user.full_name if user else "Traveller")
    guardian_name = payload.get("guardian_name")
    guardian_contact = payload.get("guardian_contact")
    destination = payload.get("destination")
    expected_arrival = payload.get("expected_arrival")
    start_lat = payload.get("latitude")
    start_lng = payload.get("longitude")

    if not guardian_name or not guardian_contact or not destination or not expected_arrival:
        raise HTTPException(status_code=400, detail="Missing journey parameters")

    tracking_code = str(uuid.uuid4())[:8].upper()

    journey = models.GuardianJourney(
        user_id=user.id if user else None,
        traveller_name=traveller_name,
        guardian_name=guardian_name,
        guardian_contact=guardian_contact,
        destination=destination,
        expected_arrival=expected_arrival,
        current_lat=float(start_lat) if start_lat else None,
        current_lng=float(start_lng) if start_lng else None,
        status="Active",
        tracking_code=tracking_code
    )
    db.add(journey)
    db.commit()
    db.refresh(journey)

    return JSONResponse({
        "status": "success",
        "message": "Guardian Journey activated!",
        "journey_id": journey.id,
        "tracking_code": tracking_code,
        "tracking_url": f"/guardian/track/{tracking_code}"
    })

@router.post("/api/journey/location")
async def update_journey_location(
    payload: dict = Body(...),
    db: Session = Depends(get_db)
):
    tracking_code = payload.get("tracking_code")
    lat = payload.get("latitude")
    lng = payload.get("longitude")

    if not tracking_code or lat is None or lng is None:
        raise HTTPException(status_code=400, detail="Invalid location data")

    journey = db.query(models.GuardianJourney).filter(models.GuardianJourney.tracking_code == tracking_code).first()
    if not journey:
        raise HTTPException(status_code=404, detail="Journey not found")

    journey.current_lat = float(lat)
    journey.current_lng = float(lng)
    journey.updated_at = datetime.utcnow()
    db.commit()

    return {"status": "success", "message": "Location updated"}

@router.post("/api/journey/complete")
async def complete_journey(
    payload: dict = Body(...),
    db: Session = Depends(get_db)
):
    tracking_code = payload.get("tracking_code")
    journey = db.query(models.GuardianJourney).filter(models.GuardianJourney.tracking_code == tracking_code).first()
    if not journey:
        raise HTTPException(status_code=404, detail="Journey not found")

    journey.status = "Completed"
    journey.updated_at = datetime.utcnow()
    db.commit()

    return {"status": "success", "message": "Journey marked as Completed! Glad you reached safely."}

@router.get("/api/journey/track/{tracking_code}")
def get_journey_tracking(
    tracking_code: str,
    db: Session = Depends(get_db)
):
    journey = db.query(models.GuardianJourney).filter(models.GuardianJourney.tracking_code == tracking_code).first()
    if not journey:
        raise HTTPException(status_code=404, detail="Journey not found")

    return {
        "id": journey.id,
        "traveller_name": journey.traveller_name,
        "guardian_name": journey.guardian_name,
        "guardian_contact": journey.guardian_contact,
        "destination": journey.destination,
        "expected_arrival": journey.expected_arrival,
        "current_lat": journey.current_lat,
        "current_lng": journey.current_lng,
        "status": journey.status,
        "tracking_code": journey.tracking_code,
        "updated_at": journey.updated_at.strftime("%I:%M:%S %p") if journey.updated_at else "Just now"
    }
