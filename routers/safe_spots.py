from fastapi import APIRouter, Depends, Request, Form, Body, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from database import get_db
import models

router = APIRouter()

@router.get("/api/safe-spots")
def get_safe_spots(db: Session = Depends(get_db)):
    spots = db.query(models.SafeSpot).filter(models.SafeSpot.verified == True).all()
    res = []
    for s in spots:
        res.append({
            "id": s.id,
            "name": s.name,
            "spot_type": s.spot_type,
            "latitude": s.latitude,
            "longitude": s.longitude,
            "address": s.address,
            "phone": s.phone or "N/A",
            "verified": s.verified
        })
    return res

@router.post("/api/safe-spots")
def create_safe_spot(
    name: str = Form(...),
    spot_type: str = Form(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    address: str = Form(...),
    phone: str = Form(""),
    db: Session = Depends(get_db)
):
    new_spot = models.SafeSpot(
        name=name.strip(),
        spot_type=spot_type,
        latitude=latitude,
        longitude=longitude,
        address=address.strip(),
        phone=phone.strip() if phone else None,
        verified=True
    )
    db.add(new_spot)
    db.commit()
    db.refresh(new_spot)

    return JSONResponse({
        "status": "success",
        "message": f"Safe Spot '{name}' added successfully!",
        "spot_id": new_spot.id
    })
