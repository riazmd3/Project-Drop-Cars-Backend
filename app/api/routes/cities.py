from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict

from app.database.session import get_db
from app.core.security import get_current_vendor, get_current_vehicleOwner_id
from app.utils.cities import get_cities
from app.models.notification import Notification

router = APIRouter(prefix="/cities")


@router.get("/vendor", response_model=List[str])
def list_cities_for_vendor(
    _: str = Depends(get_current_vendor),
):
    return get_cities()


@router.get("/vehicle-owner/selected", response_model=Dict[str, bool])
def get_selected_cities_vehicle_owner(
    db: Session = Depends(get_db),
    vehicle_owner_id: str = Depends(get_current_vehicleOwner_id),
):
    cities = get_cities()
    notif = db.query(Notification).filter(
        Notification.user == "vehicle_owner",
        Notification.sub == vehicle_owner_id
    ).first()
    selected = set((notif.selected_city or [])) if notif else set()
    return {city: (city in selected) for city in cities}


class SelectedCitiesPayload(Dict[str, List[str]]):
    # Placeholder typing for FastAPI docs; we will validate at runtime
    pass


@router.post("/vehicle-owner/selected", response_model=Dict[str, List[str]])
def update_selected_cities_vehicle_owner(
    payload: List[str],
    db: Session = Depends(get_db),
    vehicle_owner_id: str = Depends(get_current_vehicleOwner_id),
):
    # Basic validation: ensure all entries are strings and exist in the master list
    cities = set(get_cities())
    invalid = [c for c in payload if not isinstance(c, str) or c not in cities]
    if invalid:
        raise HTTPException(status_code=400, detail=f"Invalid city names: {invalid}")

    notif = db.query(Notification).filter(
        Notification.user == "vehicle_owner",
        Notification.sub == vehicle_owner_id
    ).first()

    if not notif:
        notif = Notification(
            user="vehicle_owner",
            sub=vehicle_owner_id,
            permission1=False,
            permission2=False,
            token=None,
            selected_city=list(dict.fromkeys(payload))
        )
        db.add(notif)
    else:
        notif.selected_city = list(dict.fromkeys(payload))

    db.commit()
    db.refresh(notif)
    return {"selected_city": notif.selected_city or []}


