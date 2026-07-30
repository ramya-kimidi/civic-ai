from sqlalchemy.orm import Session
import models
from auth_utils import hash_password

def seed_database(db: Session):
    # Seed Users
    if db.query(models.User).count() == 0:
        default_users = [
            models.User(
                username="citizen",
                email="citizen@smartcivic.org",
                hashed_password=hash_password("citizen123"),
                full_name="Jane Doe (Citizen)",
                phone="+1 (555) 019-2834",
                role="citizen"
            ),
            models.User(
                username="cityadmin",
                email="cityadmin@smartcivic.org",
                hashed_password=hash_password("admin123"),
                full_name="Alex Vance (City Manager)",
                phone="+1 (555) 012-3456",
                role="city_admin"
            ),
            models.User(
                username="emergencyadmin",
                email="emergencyadmin@smartcivic.org",
                hashed_password=hash_password("admin123"),
                full_name="Cmdr. Marcus Hill (Dispatcher)",
                phone="+1 (555) 018-9900",
                role="emergency_admin"
            )
        ]
        db.add_all(default_users)
        db.commit()
        print("✅ Default users seeded successfully.")

    # Seed Safe Spots
    if db.query(models.SafeSpot).count() == 0:
        default_spots = [
            models.SafeSpot(
                name="Metro Central City Hospital",
                spot_type="Hospital",
                latitude=28.6139,
                longitude=77.2090,
                address="102 Health Avenue, Downtown Civic Center",
                phone="+1 (800) 555-0199",
                verified=True
            ),
            models.SafeSpot(
                name="Central District Police HQ",
                spot_type="Police Station",
                latitude=28.6189,
                longitude=77.2150,
                address="45 Precinct Plaza, City Center",
                phone="+1 (800) 555-0100",
                verified=True
            ),
            models.SafeSpot(
                name="Station 1 Fire & Rescue",
                spot_type="Fire Station",
                latitude=28.6089,
                longitude=77.2020,
                address="12 Rescue Boulevard, South Sector",
                phone="+1 (800) 555-0119",
                verified=True
            ),
            models.SafeSpot(
                name="Community Civic Shelter & Relief Hub",
                spot_type="Shelter",
                latitude=28.6210,
                longitude=77.2210,
                address="78 Haven Road, East District",
                phone="+1 (800) 555-0144",
                verified=True
            ),
            models.SafeSpot(
                name="24x7 Express Care Pharmacy",
                spot_type="Pharmacy",
                latitude=28.6110,
                longitude=77.2180,
                address="33 Main Street, West End",
                phone="+1 (800) 555-0177",
                verified=True
            ),
            models.SafeSpot(
                name="St. Mary Emergency Care",
                spot_type="Hospital",
                latitude=28.6250,
                longitude=77.2010,
                address="200 Medical Park Drive",
                phone="+1 (800) 555-0188",
                verified=True
            )
        ]
        db.add_all(default_spots)
        db.commit()
        print("✅ Default safe spots seeded successfully.")

    # Seed an active sample disaster for demonstration
    if db.query(models.Disaster).count() == 0:
        default_disaster = models.Disaster(
            disaster_type="Flood",
            title="Heavy Urban Flooding & Waterlogging",
            area="Downtown Riverbed & Low-lying Sectors",
            description="Flash flood warning issued due to relentless heavy rainfall. Water levels reaching 3 feet in underpasses. Citizens are advised to stay indoors and avoid low-lying roads.",
            severity="High",
            latitude=28.6150,
            longitude=77.2110,
            is_active=True
        )
        db.add(default_disaster)
        db.commit()
        print("✅ Default sample disaster seeded.")
