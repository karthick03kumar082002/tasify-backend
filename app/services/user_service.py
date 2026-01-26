import os
import uuid
import re
from datetime import date
from typing import Optional
from pathlib import Path
import asyncio
from sqlalchemy import select, desc
from app.utils.mailer import user_registered
from fastapi import UploadFile, BackgroundTasks, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from passlib.context import CryptContext
import cloudinary.uploader

from app.models.users import AuthUser
from app.core.response import AppException
from typing import List
# Password hashing
pass_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
MAX_BCRYPT_BYTES = 72

# Image upload
ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
BASE_UPLOAD_DIR = "uploads"
PROFILE_IMAGE = "profile_image"
def normalize_image_url(path: str | None):
    return path.replace("\\", "/") if path else None
def hash_password(password: str) -> str:
    """
    Hash password safely for bcrypt.
    Truncate to 72 bytes because bcrypt cannot handle more.
    """
    password_bytes = password.encode("utf-8")
    if len(password_bytes) > MAX_BCRYPT_BYTES:
        password_bytes = password_bytes[:MAX_BCRYPT_BYTES]
    truncated_password = password_bytes.decode("utf-8", errors="ignore")
    return pass_context.hash(truncated_password)

def validate_password(password: str):
    """
    Validate password strength and length.
    """
    password_bytes = password.encode("utf-8")
    if len(password_bytes) < 8:
        raise AppException(
            message="Password must be at least 8 characters long",
            error="WEAK_PASSWORD",
        )

    if len(password_bytes) > MAX_BCRYPT_BYTES:
        raise AppException(
            message=f"Password must not exceed {MAX_BCRYPT_BYTES} bytes",
            error="PASSWORD_TOO_LONG",
        )

    if not re.search(r"[A-Z]", password):
        raise AppException(
            message="Password must contain at least one uppercase letter",
            error="WEAK_PASSWORD",
        )

    if not re.search(r"[a-z]", password):
        raise AppException(
            message="Password must contain at least one lowercase letter",
            error="WEAK_PASSWORD",
        )

    if not re.search(r"\d", password):
        raise AppException(
            message="Password must contain at least one number",
            error="WEAK_PASSWORD",
        )

    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        raise AppException(
            message="Password must contain at least one special character",
            error="WEAK_PASSWORD",
        )

    return True

async def save_media(file: UploadFile, folder: str):
    if not file:
        return None

    result = cloudinary.uploader.upload(
        file.file,
        folder=folder,
        resource_type="image"
    )

    return result["secure_url"]
class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db
# ---------------- create users ----------------
    async def create_user_form(
        self,
        background_tasks: BackgroundTasks,
        first_name: str,
        last_name: str,
        dob: date,
        email: str,
        password: str,
        phone_number: Optional[str],
        profile_image: Optional[UploadFile],
    ):
        # ---------------- EMAIL CHECK ----------------
        result = await self.db.execute(select(AuthUser).where(AuthUser.email == email))
        existing = result.scalars().first()
        if existing:
            raise AppException(
                message="Email already exists",
                error="DUPLICATE_EMAIL",
                status_code=status.HTTP_400_BAD_REQUEST,
            )


        # ---------------- FULL NAME ----------------
        full_name = f"{first_name.strip()} {last_name.strip()}"

        # ---------------- AGE ----------------
        today = date.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        if age < 18:
            raise AppException(
                message="User must be at least 18 years old",
                error="UNDERAGE",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        # ---------------- PROFILE IMAGE ----------------
        image_path=None
        if profile_image:
           image_path = await save_media(profile_image, folder="taskify/profile")

        # ---------------- HASH PASSWORD ----------------
        try:
                   
            validate_password(password)
            hashed_password = hash_password(password)

        # ---------------- SAVE USER ----------------
            new_user = AuthUser(
                full_name=full_name,
                first_name=first_name,
                last_name=last_name,
                dob=dob,
                age=age,
                email=email,
                phone_number=phone_number,
                password=hashed_password,
                profile_image=image_path,
                is_active=True,
            )

            self.db.add(new_user)
            await self.db.commit()
            await self.db.refresh(new_user)
            asyncio.create_task(
                user_registered(
                    to_email=new_user.email,
                    full_name=new_user.full_name
                )
            )

            # ---------------- SUCCESS RESPONSE ----------------
            return {
                "success": True,
                "message": "User created successfully",
                "data": {
                    "id": new_user.id,
                    "full_name": new_user.full_name,
                    "email": new_user.email,
                    "age": new_user.age,
                    "profile_image": new_user.profile_image,
                },
                "error": None,
            }

        
        except AppException as e:
            await self.db.rollback()
            raise e
        
        except Exception as e:
            await self.db.rollback()
            raise AppException(
                message="Unexpected error occurred",
                error=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    # ---------------- GET ALL USERS ----------------
    async def get_all_users(self):
        result = await self.db.execute(select(AuthUser).order_by(desc(AuthUser.id)))
        users = result.scalars().all()

        user_list = [
            {
                "id": user.id,
                "full_name": user.full_name,
                "email": user.email,
                "age": user.age,
                "profile_image": user.profile_image,
            }
            for user in users
        ]

        return {
            "success": True,
            "message": "Users fetched successfully",
            "data": user_list,
            "error": None,
        }



    # ---------------- GET USER BY ID ----------------
    async def get_user_by_id(self, user_id: int) -> AuthUser:
        result = await self.db.execute(select(AuthUser).where(AuthUser.id == user_id))
        user = result.scalars().first()
        if not user:
            raise AppException(message="User not found", error="NOT_FOUND", status_code=404)
        user_list = [
            {
                "id": user.id,
                "full_name": user.full_name,
                "email": user.email,
                "age": user.age,
                "profile_image": user.profile_image,
            }   
        ]
        return {
            "success": True,
            "message": "User fetched successfully",
            "data": user_list,
            "error": None,
        }
    # ---------------- UPDATE USERS ----------------
    async def update_user(
        self,
        user_id: int,
        current_user:int,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        dob: Optional[date] = None,
        phone_number: Optional[str] = None,
        password: Optional[str] = None,
        profile_image: Optional[UploadFile] = None,
    ):
        if current_user.id != user_id:
            raise AppException(
                message="You are not allowed to update this user",
                error="Unauthorized_Access",
                status_code=403,
            )
        result = await self.db.execute(select(AuthUser).where(AuthUser.id == user_id))
        user = result.scalars().first()
        if not user:
            raise AppException(message="User not found", error="NOT_FOUND", status_code=404)

        # Update fields
        if first_name is not None:
            user.first_name = first_name
        if last_name is not None:
            user.last_name = last_name
        if first_name or last_name:
            user.full_name = f"{user.first_name} {user.last_name}"

        if dob is not None:
            user.dob = dob
            today = date.today()
            user.age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

        if phone_number is not None:
            user.phone_number = phone_number

        # Update profile image if provided
        if profile_image is not None:
            ext = profile_image.filename.split(".")[-1].lower()
            if ext not in ALLOWED_IMAGE_EXTENSIONS:
                raise AppException(
                    message="Invalid image format",
                    error=f"Allowed: {ALLOWED_IMAGE_EXTENSIONS}",
                    status_code=400,
                )
            
            image=await save_media(profile_image, sub_folder="profile")
            image_path=normalize_image_url(image)
            user.profile_image=image_path
           

        await self.db.commit()
        await self.db.refresh(user)

        return {
            "success": True,
            "message": "User updated successfully",
            "data": {
                "id": user.id,
                "full_name": user.full_name,
                "email": user.email,
                "age": user.age,
                "profile_image": user.profile_image,
            },
            "error": None,
        }
    # ---------------- DELETE USERS ----------------
    async def delete_user(self, user_id: int):
        result = await self.db.execute(select(AuthUser).where(AuthUser.id == user_id))
        user = result.scalars().first()
        if not user:
            raise AppException(message="User not found", error="NOT_FOUND", status_code=404)

        await self.db.delete(user)
        await self.db.commit()

        return {
            "success": True,
            "message": "User deleted successfully",
            "data": None,
            "error": None,
        }
