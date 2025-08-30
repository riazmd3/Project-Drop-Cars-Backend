from fastapi import FastAPI
from app.api.routes import vendor, vehicle_owner, car_details, car_driver, new_orders, order_assignments
import app.models.admin
import app.models.car_driver
import app.models.vehicle_owner
import app.models.vehicle_owner_details
import app.models.car_details
import app.models.vendor
import app.models.new_orders
import app.models.vendor_details
import app.models.order_assignments
from app.database.session import Base, engine

# Create DB tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Auth API")

app.include_router(vendor.router, prefix="/api/users", tags=["Vendors"])
app.include_router(vehicle_owner.router, prefix="/api/users", tags=["VehicleOwner"])
app.include_router(car_details.router, prefix="/api/users", tags=["CarDetails"])
app.include_router(car_driver.router, prefix="/api/users", tags=["CarDriver"])
app.include_router(new_orders.router, prefix="/api/orders", tags=["NewOrders"])
app.include_router(order_assignments.router, prefix="/api/assignments", tags=["OrderAssignments"])
app.include_router(order_assignments.router, prefix="/api/orders", tags=["OrderAssignments"])

