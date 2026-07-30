from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    role = Column(String, default="citizen") # "citizen", "city_admin", "emergency_admin"
    created_at = Column(DateTime, default=datetime.utcnow)

    alerts = relationship("Alert", back_populates="user")
    emergency_requests = relationship("EmergencyRequest", back_populates="user")
    guardian_journeys = relationship("GuardianJourney", back_populates="user")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    alert_type = Column(String, nullable=False) # "SOS", "Accident"
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    address = Column(String, nullable=True)
    status = Column(String, default="Pending") # "Pending", "Accepted", "Responding", "Resolved"
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="alerts")


class Disaster(Base):
    __tablename__ = "disasters"

    id = Column(Integer, primary_key=True, index=True)
    disaster_type = Column(String, nullable=False) # "Flood", "Fire", "Cyclone", "Heavy Rainfall", "Building Collapse", "Other"
    title = Column(String, nullable=False)
    area = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(String, default="Medium") # "Low", "Medium", "High", "Critical"
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)


class EmergencyRequest(Base):
    __tablename__ = "emergency_requests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    request_type = Column(String, nullable=False) # "Ambulance", "Fire", "Police", "Rescue"
    description = Column(Text, nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    status = Column(String, default="Pending") # "Pending", "Accepted", "On The Way", "Resolved"
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="emergency_requests")


class GuardianJourney(Base):
    __tablename__ = "guardian_journeys"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    traveller_name = Column(String, nullable=False)
    guardian_name = Column(String, nullable=False)
    guardian_contact = Column(String, nullable=False)
    destination = Column(String, nullable=False)
    expected_arrival = Column(String, nullable=False)
    current_lat = Column(Float, nullable=True)
    current_lng = Column(Float, nullable=True)
    status = Column(String, default="Active") # "Active", "Completed", "Emergency", "Cancelled"
    tracking_code = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="guardian_journeys")


class SafeSpot(Base):
    __tablename__ = "safe_spots"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    spot_type = Column(String, nullable=False) # "Hospital", "Police Station", "Fire Station", "Shelter", "Pharmacy"
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    address = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    verified = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
