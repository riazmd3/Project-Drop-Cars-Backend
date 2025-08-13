from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from app.schemas.vehicle_owner import VehicleOwnerBase
from app.crud.vehicle_owner import create_user
from app.database.session import get_db
from app.utils.gcs import upload_image_to_gcs  # Utility function you need to implement

router = APIRouter()

@router.post("/vehicleowner/signup")
async def signup(
    full_name: str = Form(...),
    primary_number: str = Form(...),
    secondary_number: str = Form(...),
    password: str = Form(...),
    address: str = Form(...),
    gpay_number: str = Form(...),
    aadhar_number: str = Form(...),
    organization_id: str = Form(None),
    aadhar_front_img: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    # Upload image file to GCS and get public URL
    try:
        aadhar_img_url = upload_image_to_gcs(aadhar_front_img)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image upload failed: {e}")

    # Create Pydantic model instance with public URL of image
    user_in = VehicleOwnerBase(
        full_name=full_name,
        primary_number=primary_number,
        secondary_number=secondary_number,
        password=password,
        address=address,
        gpay_number=gpay_number,
        aadhar_number=aadhar_number,
        organization_id=organization_id,
        aadhar_front_img=aadhar_img_url,
    )

    # Call your existing create_user function to save user to DB
    db_user = create_user(db, user_in)

    return {"msg": "User created successfully", "user_id": str(db_user.id), "aadhar_img_url": aadhar_img_url}


# @router.post("/vehicleowner/login")
# def login(user: UserLogin, db: Session = Depends(get_db)):
#     db_user = authenticate_user(db, user.mobile_number, user.password)
#     if not db_user:
#         raise HTTPException(status_code=400, detail="Invalid credentials")
#     access_token = create_access_token({"sub": str(db_user.id)})
#     return {"access_token": access_token, "token_type": "bearer"}
