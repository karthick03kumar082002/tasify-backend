from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import get_db
from app.services.password_service import PasswordService
from app.schema.password_schema import ForgotPasswordRequest,VerifyOTPRequest,ResetPasswordRequest,TokenResetPasswordRequest
router = APIRouter()



# --------------------------------------------------
#  Send OTP to Email
# -------------------------------------------------
@router.post("/send_otp")
async def send_otp(request: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    service=PasswordService(db)
    return await service.send_otp(request.email)
# -------------------------------------------------
# Verify OTP
# -------------------------------------------------
@router.post("/verify_otp")
async def verify_otp(request:VerifyOTPRequest, db: AsyncSession = Depends(get_db)):
    service=PasswordService(db)
    return await service.verify_otp(request.email, request.otp)
# ---------------------------------------------------
#  Reset Password Using OTP
# ---------------------------------------------------
@router.post("/reset_password")
async def reset_password(request:ResetPasswordRequest, 
                         db: AsyncSession = Depends(get_db)):
    service=PasswordService(db)
    return await service.reset_password(request.email, request.new_password, request.confirm_password)
