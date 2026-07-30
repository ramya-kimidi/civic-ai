from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from database import get_db
import models

router = APIRouter()

@router.get("/api/admin/stats")
def get_admin_stats(db: Session = Depends(get_db)):
    total_alerts = db.query(models.Alert).count()
    pending_alerts = db.query(models.Alert).filter(models.Alert.status == "Pending").count()
    total_transport_reqs = db.query(models.EmergencyRequest).count()
    pending_transport_reqs = db.query(models.EmergencyRequest).filter(models.EmergencyRequest.status == "Pending").count()
    resolved_cases = db.query(models.Alert).filter(models.Alert.status == "Resolved").count() + \
                     db.query(models.EmergencyRequest).filter(models.EmergencyRequest.status == "Resolved").count()
    active_disasters = db.query(models.Disaster).filter(models.Disaster.is_active == True).count()
    active_journeys = db.query(models.GuardianJourney).filter(models.GuardianJourney.status == "Active").count()

    return {
        "total_alerts": total_alerts,
        "pending_alerts": pending_alerts,
        "total_transport_reqs": total_transport_reqs,
        "pending_transport_reqs": pending_transport_reqs,
        "resolved_cases": resolved_cases,
        "active_disasters": active_disasters,
        "active_journeys": active_journeys
    }
