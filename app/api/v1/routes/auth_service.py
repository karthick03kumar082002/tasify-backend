# routes.py
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import get_db
from app.schema.login_schema import LoginRequest,RefreshTokenRequest
from app.services.auth_service import AuthService
from app.utils.jwt import get_current_user

router = APIRouter()
@router.post("/login/")
async def login(request: Request, payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    return await service.login(payload.email, payload.password,request)

@router.post("/logout/")
async def logout(request: Request, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    return await service.logout(request)

@router.post("/refresh/")
async def refresh_token(payload: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    return await service.refresh_access_token(payload)