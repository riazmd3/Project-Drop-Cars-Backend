from fastapi import FastAPI
from app.api.routes import vendor,driver, vehicle_owner
import app.models.admin
from app.database.session import Base, engine

# Create DB tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Auth API")

app.include_router(vendor.router, prefix="/api/users", tags=["Vendors"])
app.include_router(driver.router, prefix="/api/users", tags=["Drivers"])
app.include_router(vehicle_owner.router, prefix="/api/users", tags=["VehicleOwner"])

