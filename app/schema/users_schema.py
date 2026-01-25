from pydantic import BaseModel, EmailStr
from datetime import date, datetime
from typing import Optional

class UserResponse(BaseModel):
    id: int
    full_name: str
    email: str
    age: int
    profile_image: Optional[str]

    class Config:
        orm_mode = True

class UserUpdateRequest(BaseModel):
    first_name: Optional[str]
    last_name: Optional[str]
    dob: Optional[date]
    phone_number: Optional[str]