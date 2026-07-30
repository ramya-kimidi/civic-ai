import uvicorn
from fastapi import FastAPI, Request, Depends, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session

from database import engine, Base, get_db
import models
from seed_data import seed_database
from auth_utils import get_current_user

# Import Routers
from routers import auth, alerts, disasters, transport, guardian, safe_spots, admin

# Initialize Database tables
Base.metadata.create_all(bind=engine)

# Seed initial default data (Users, Safe Spots, Sample Disaster)
with Session(engine) as init_db:
    seed_database(init_db)

app = FastAPI(title="SmartCivic - Urban Safety & Emergency Assistance Platform")

# Add Session Middleware for cookie sessions
app.add_middleware(SessionMiddleware, secret_key="smartcivic_session_secret_key_2026")

# Mount Static Files and Jinja2 Templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Include Routers
app.include_router(auth.router)
app.include_router(alerts.router)
app.include_router(disasters.router)
app.include_router(transport.router)
app.include_router(guardian.router)
app.include_router(safe_spots.router)
app.include_router(admin.router)

# Helper to pass template context with flash messages & logged in user
def render_template(template_name: str, request: Request, db: Session, context: dict = None):
    if context is None:
        context = {}
    
    current_user = get_current_user(request, db)
    flash_error = request.session.pop("flash_error", None)
    flash_success = request.session.pop("flash_success", None)

    context.update({
        "user": current_user,
        "flash_error": flash_error,
        "flash_success": flash_success
    })
    return templates.TemplateResponse(request=request, name=template_name, context=context)

# ---------------- ROUTE HANDLERS ---------------- #

@app.get("/", response_class=HTMLResponse)
def index_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if user:
        if user.role == "city_admin":
            return RedirectResponse(url="/city-admin/dashboard")
        elif user.role == "emergency_admin":
            return RedirectResponse(url="/emergency-admin/dashboard")
        else:
            return RedirectResponse(url="/user/dashboard")
    return render_template("index.html", request, db)

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if user:
        return RedirectResponse(url="/profile")
    return render_template("login.html", request, db)

@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if user:
        return RedirectResponse(url="/profile")
    return render_template("register.html", request, db)

@app.get("/profile", response_class=HTMLResponse)
def profile_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    total_alerts = 0
    total_requests = 0
    my_alerts = []
    my_requests = []
    active_journey = None

    if user:
        my_alerts = db.query(models.Alert).filter(models.Alert.user_id == user.id).order_by(models.Alert.created_at.desc()).all()
        my_requests = db.query(models.EmergencyRequest).filter(models.EmergencyRequest.user_id == user.id).order_by(models.EmergencyRequest.created_at.desc()).all()
        active_journey = db.query(models.GuardianJourney).filter(models.GuardianJourney.user_id == user.id, models.GuardianJourney.status == "Active").first()
        total_alerts = len(my_alerts)
        total_requests = len(my_requests)

    return render_template("profile.html", request, db, {
        "total_alerts": total_alerts,
        "total_requests": total_requests,
        "my_alerts": my_alerts,
        "my_requests": my_requests,
        "active_journey": active_journey
    })

@app.get("/user/dashboard", response_class=HTMLResponse)
def user_dashboard(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    
    # Active disasters count
    active_disasters_count = db.query(models.Disaster).filter(models.Disaster.is_active == True).count()
    
    # User specific active items
    my_recent_alerts = []
    my_recent_requests = []
    my_active_journey = None

    if user:
        my_recent_alerts = db.query(models.Alert).filter(models.Alert.user_id == user.id).order_by(models.Alert.created_at.desc()).limit(5).all()
        my_recent_requests = db.query(models.EmergencyRequest).filter(models.EmergencyRequest.user_id == user.id).order_by(models.EmergencyRequest.created_at.desc()).limit(5).all()
        my_active_journey = db.query(models.GuardianJourney).filter(models.GuardianJourney.user_id == user.id, models.GuardianJourney.status == "Active").first()

    return render_template("user_dashboard.html", request, db, {
        "active_disasters_count": active_disasters_count,
        "my_recent_alerts": my_recent_alerts,
        "my_recent_requests": my_recent_requests,
        "my_active_journey": my_active_journey
    })

@app.get("/accident", response_class=HTMLResponse)
def accident_page(request: Request, db: Session = Depends(get_db)):
    return render_template("accident.html", request, db)

@app.get("/disasters", response_class=HTMLResponse)
def disasters_page(request: Request, db: Session = Depends(get_db)):
    disasters = db.query(models.Disaster).filter(models.Disaster.is_active == True).order_by(models.Disaster.created_at.desc()).all()
    return render_template("disasters.html", request, db, {"disasters": disasters})

@app.get("/transport", response_class=HTMLResponse)
def transport_page(request: Request, db: Session = Depends(get_db)):
    return render_template("transport.html", request, db)

@app.get("/guardian", response_class=HTMLResponse)
def guardian_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    active_journey = None
    if user:
        active_journey = db.query(models.GuardianJourney).filter(
            models.GuardianJourney.user_id == user.id,
            models.GuardianJourney.status == "Active"
        ).first()

    return render_template("guardian.html", request, db, {"active_journey": active_journey})

@app.get("/guardian/track/{tracking_code}", response_class=HTMLResponse)
def guardian_track_page(tracking_code: str, request: Request, db: Session = Depends(get_db)):
    journey = db.query(models.GuardianJourney).filter(models.GuardianJourney.tracking_code == tracking_code).first()
    if not journey:
        return RedirectResponse(url="/user/dashboard")
    return render_template("guardian_track.html", request, db, {"journey": journey})

@app.get("/safe-spots", response_class=HTMLResponse)
def safe_spots_page(request: Request, db: Session = Depends(get_db)):
    return render_template("safe_spots.html", request, db)

@app.get("/city-admin/dashboard", response_class=HTMLResponse)
def city_admin_dashboard(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role != "city_admin":
        request.session["flash_error"] = "City Administrator access required."
        return RedirectResponse(url="/login")

    disasters = db.query(models.Disaster).order_by(models.Disaster.created_at.desc()).all()
    return render_template("city_admin_dashboard.html", request, db, {"disasters": disasters})

@app.get("/emergency-admin/dashboard", response_class=HTMLResponse)
def emergency_admin_dashboard(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role != "emergency_admin":
        request.session["flash_error"] = "Emergency Administrator access required."
        return RedirectResponse(url="/login")

    return render_template("emergency_admin_dashboard.html", request, db)

@app.get("/emergency-admin/alerts", response_class=HTMLResponse)
def emergency_alerts_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role != "emergency_admin":
        return RedirectResponse(url="/login")

    alerts = db.query(models.Alert).order_by(models.Alert.created_at.desc()).all()
    return render_template("alerts.html", request, db, {"alerts": alerts})

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=3000, reload=True)
