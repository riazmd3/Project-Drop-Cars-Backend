from fastapi import FastAPI
from fastapi_utils.tasks import repeat_every
from app.database.session import SessionLocal
from app.api.routes import vendor, vehicle_owner, car_details, car_driver, new_orders, order_assignments, transfer_transactions, admin, hourly_rental, orders, wallet, notification
import app.models.admin
import app.models.car_driver
import app.models.vehicle_owner
import app.models.vehicle_owner_details
import app.models.car_details
import app.models.vendor
import app.models.new_orders
import app.models.vendor_details
import app.models.hourly_rental
import app.models.orders
import app.models.order_assignments
import app.models.transfer_transactions
import app.models.wallet_ledger
import app.models.razorpay_transactions
import app.models.vendor_wallet_ledger
import app.models.admin_wallet_ledger
import app.models.admin_add_money_to_vehicle_owner
from app.database.session import Base, engine
import app.models.end_records

# Create DB tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Auth API")

app.include_router(vendor.router, prefix="/api/users", tags=["Vendors"])
app.include_router(vehicle_owner.router, prefix="/api/users", tags=["VehicleOwner"])
app.include_router(car_details.router, prefix="/api/users", tags=["CarDetails"])
app.include_router(car_driver.router, prefix="/api/users", tags=["CarDriver"])
app.include_router(new_orders.router, prefix="/api/orders", tags=["NewOrders"])
app.include_router(hourly_rental.router, prefix="/api/orders", tags=["HourlyRental"])
app.include_router(orders.router, prefix="/api/orders", tags=["Orders"])
app.include_router(order_assignments.router, prefix="/api/assignments", tags=["OrderAssignments"])
app.include_router(order_assignments.router, prefix="/api/orders", tags=["OrderAssignments"])
app.include_router(transfer_transactions.router, prefix="/api", tags=["TransferTransactions"])
app.include_router(admin.router, prefix="/api", tags=["Admin"])
app.include_router(wallet.router, prefix="/api", tags=["Wallet"]) 
app.include_router(notification.router, prefix="/api", tags=["notifications"]) 



@app.on_event("startup")
@repeat_every(seconds=60, wait_first=True)  # every 3 minutes
async def cancel_expired_assignments_task() -> None:
    """Background job: cancel pending assignments that exceeded their max assignment time."""
    db = SessionLocal()
    try:
        from app.crud.order_assignments import cancel_timed_out_pending_assignments
        cancelled = await cancel_timed_out_pending_assignments(db)
        if cancelled:
            print(f"Auto-cancelled {cancelled} timed-out assignment(s)")
    finally:
        db.close()

