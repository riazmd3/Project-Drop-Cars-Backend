from pydantic import BaseModel
from typing import Optional

class NotificationBase(BaseModel):
    permission1: Optional[bool] = False
    permission2: Optional[bool] = False
    token: Optional[str] = None

class NotificationCreate(NotificationBase):
    pass

class NotificationUpdate(NotificationBase):
    pass

class NotificationResponse(NotificationBase):
    sub: str

    class Config:
        orm_mode = True

class NotificationPermissionUpdate(BaseModel):
    permission1: Optional[bool] = None
    permission2: Optional[bool] = None

