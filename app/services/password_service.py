import random,asyncio,math
from math import ceil
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import status,BackgroundTasks
from app.models.users import AuthUser,RevokedToken
from app.models.password import PasswordOTP
from app.utils.mailer import send_otp
from app.core.response import AppException
from passlib.context import CryptContext
from app.services.user_service import validate_password
from app.validations.strong_pass import strongPassword


# ------------------------------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
OTP_EXPIRY_MINUTES= 3

# ==============================================================
#  TIME  functions
# ==============================================================
def get_expiry(minutes: int = OTP_EXPIRY_MINUTES):
    """Returns expiry datetime for given minutes."""
    return datetime.utcnow() + timedelta(minutes=minutes)

def get_remaining_minutes(expiry_time: datetime):
    """Returns remaining minutes until expiry."""
    remaining_seconds = (expiry_time - datetime.utcnow()).total_seconds()
    return max(0, ceil(remaining_seconds / 60))
def get_link_expiry():
    return datetime.utcnow() + timedelta(minutes=5)

class PasswordService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # -------------------------------------------------------
    # 1️. Send OTP to Email
    # -------------------------------------------------------
    async def send_otp(self, background_tasks: BackgroundTasks, email: str,):
        print(f"[OTP] Request received for email: {email}")

        user = await self.db.scalar(select(AuthUser).where(AuthUser.email == email))
        if not user:
            print(f"[OTP] ❌ User not found for email: {email}")
            raise AppException(
                message="Email Not Found",
                error="Invalid Email",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        existing_otp = await self.db.scalar(
            select(PasswordOTP).where(
                PasswordOTP.email == email,
                PasswordOTP.type == "otp"
            )
        )

        now = datetime.utcnow()
        otp = random.randint(100000, 999999)
        expiry = get_expiry()

        print(f"[OTP] Generated OTP: {otp} | Expires at: {expiry}")

        if existing_otp and existing_otp.expires_at > now:
            remaining = get_remaining_minutes(existing_otp.expires_at)
            print(f"[OTP] ⚠ OTP already valid for {remaining} more minute(s)")
            raise AppException(
                message=f"OTP already sent. Try again after {remaining} minute(s).",
                error="OTP already valid",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        if existing_otp:
            print("[OTP] Updating existing OTP record")
            existing_otp.otp = otp
            existing_otp.is_verified = False
            existing_otp.created_at = now
            existing_otp.expires_at = expiry
        else:
            print("[OTP] Creating new OTP record")
            new_otp = PasswordOTP(
                email=email,
                otp=otp,
                is_verified=False,
                created_at=now,
                expires_at=expiry
            )
            self.db.add(new_otp)

        await self.db.commit()
        print("[OTP] OTP saved successfully in DB")

        print("[OTP] Scheduling email sending task")
        background_tasks.add_task(self._send_otp_email, email, otp, OTP_EXPIRY_MINUTES)

        return {
            "success": True,
            "message": "OTP Sent To Email successfully",
            "data": None,
            "error": None
        }

    async def _send_otp_email(self, email: str, otp: int, expiry_minutes: int):
        try:
            print(f"[MAIL] Sending OTP email to {email}")
            await send_otp(email, otp, expiry_minutes)
            print(f"[MAIL] ✅ OTP email sent successfully to {email}")
        except Exception as e:
            print(f"[MAIL] ❌ Failed to send OTP email to {email}")
            print(f"[MAIL] Error: {repr(e)}")

            
    # -------------------------------------------------------
    # 2. Verify OTP
    # -------------------------------------------------------
    async def verify_otp(self, email: str, otp: int):
        record = await self.db.scalar(
            select(PasswordOTP).where(PasswordOTP.email == email, PasswordOTP.type == "otp")
        )
        
        if not record:
            user = await self.db.scalar(select(AuthUser).where(AuthUser.email == email))
            if user and user.updated_at:
                raise AppException(
                        message=f"OTP Used. Please request a new one.",
                        error="OTP_NOT_FOUND",
                        status_code=400
                    )            
            raise AppException(
                message="Invalid Email",
                error="Email Not Found",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        if record.is_verified:
            raise AppException(
                    message=f"OTP verified Recently. Try again after few minute(s).",
                    error="OTP_ALREADY_VERIFIED",
                    status_code=400
                )
        if record.expires_at < datetime.utcnow():
            raise AppException(
                message="OTP expired",
                error="Invalid OTP",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        if record.otp != otp:
            raise AppException(
                message="Expired or Wrong OTP",
                error="Invalid OTP",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # mark verified
        record.is_verified = True
        await self.db.commit()

        return {
            "success": True,
            "message": "OTP verified successfully",
            "data": None,
            "error": None
        }
    # -------------------------------------------------------
    # 3️. Reset Password after OTP verification
    # -------------------------------------------------------
    async def reset_password(
        self,
        email: str,
        new_password: str,
        confirm_password: str
    ):
        # Password match
        if new_password != confirm_password:
            raise AppException(
                message="Passwords do not match",
                error="INVALID_PASSWORD",
                status_code=400
            )

        #  Validate strength
        validate_password(new_password)

        #  Fetch OTP
        otp_record = await self.db.scalar(
            select(PasswordOTP).where(
                PasswordOTP.email == email,
                PasswordOTP.type == "otp"
            )
        )

        if not otp_record:
            raise AppException(
                message="Invalid or expired OTP",
                error="INVALID_OTP",
                status_code=400
            )

        #  OTP validation
        if not otp_record.is_verified:
            raise AppException(
                message="OTP not verified",
                error="OTP_NOT_VERIFIED",
                status_code=400
            )

        if otp_record.expires_at < datetime.utcnow():
            raise AppException(
                message="OTP expired",
                error="OTP_EXPIRED",
                status_code=400
            )

        #  Fetch user
        user = await self.db.scalar(
            select(AuthUser).where(AuthUser.email == email)
        )

        if not user:
            raise AppException(
                message="User not found",
                error="INVALID_USER",
                status_code=400
            )

        #  Update password
        user.password = pwd_context.hash(new_password)
        self.db.add(user)

        #  Delete OTP
        await self.db.delete(otp_record)

        await self.db.commit()

        return {
            "success": True,
            "message": "Password updated successfully",
            "data": None,
            "error": None
        }
