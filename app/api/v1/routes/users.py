from fastapi import (
    APIRouter, Depends, UploadFile, File, Form, BackgroundTasks
)
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
from app.core.db import get_db
from app.services.user_service import UserService
from app.schema.users_schema import UserResponse
from pydantic import  EmailStr
from app.utils.jwt import get_current_user

router = APIRouter()


@router.post("/create")
async def create_user(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    first_name: str = Form(...),
    last_name: str = Form(...),
    dob: date = Form(...),
    email: EmailStr = Form(...),
    password: str = Form(...),
    phone_number: str | None = Form(None),
    profile_image: Optional[UploadFile] = File(None),
):
    service = UserService(db)

    return await service.create_user_form(
        background_tasks=background_tasks,
        first_name=first_name,
        last_name=last_name,
        dob=dob,
        email=email,
        password=password,
        phone_number=phone_number,
        profile_image=profile_image,
    )
# ---------------- GET ALL USERS ----------------
@router.get("/all")
async def get_all_users(db: AsyncSession = Depends(get_db)):
    service = UserService(db)
    return await service.get_all_users()



# ---------------- GET USER BY ID ----------------
@router.get("/{user_id}")
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    service = UserService(db)
    return await service.get_user_by_id(user_id)
   

# # ---------------- UPDATE USER ----------------


@router.put("/{user_id}")
async def update_user(
    user_id: int,
    first_name: Optional[str] = Form(None),
    last_name: Optional[str] = Form(None),
    dob: Optional[date] = Form(None),
    phone_number: Optional[str] = Form(None),
    profile_image: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    service = UserService(db)
    return await service.update_user(
        user_id=user_id,
        first_name=first_name,
        last_name=last_name,
        dob=dob,
        phone_number=phone_number,
        profile_image=profile_image,
        current_user=current_user
    )


@router.delete("/{user_id}")
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    service = UserService(db)
    return await service.delete_user(user_id)