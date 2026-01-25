import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Union
from fastapi import Request, HTTPException, status ,Depends
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from contextlib import asynccontextmanager
from app.core.db import get_db
from app.models.users import AuthUser,RevokedToken
from app.core.config import settings

# ---------------------------
# JWT Configuration
# ---------------------------
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = 7

PUBLIC_URLS: List[str] = [
   "/api/v1/user/create",
    "/api/v1/auth/login",
     "/api/v1/password/send_otp", "/api/v1/password/verify_otp", "/api/v1/password/reset_password",

    "/docs",
    "/redoc",
    "/openapi.json",
]

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login-swagger")



# ---------------------------
# Password Reset Tokens
# ---------------------------
# Generate a short-lived password reset token
def create_password_reset_token(email: str, expires_minutes: int = 5) -> str:
    payload = {
        "sub": email,
        "exp": datetime.utcnow() + timedelta(minutes=expires_minutes)
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token

# Verify token and return email
def verify_password_reset_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload.get("sub")
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


# ---------------------------
# Standard response
# ---------------------------
def standard_response(
    success: bool,
    message: str,
    data=None,
    error: str = "",
    status_code=status.HTTP_200_OK,
):
    return JSONResponse(
        status_code=status_code,
        content={
            "success": success,
            "message": message,
            "error": error,
            "data": data,
        },
    )


# ---------------------------
# JWT Utilities
# ---------------------------
def create_jwt(
    data: Dict,
    expires_delta: Union[int, timedelta, None] = None,
    refresh: bool = False,
) -> tuple[str, str]:
    jti = str(uuid.uuid4())

    if refresh:
        exp = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    else:
        if isinstance(expires_delta, timedelta):
            exp = datetime.utcnow() + expires_delta
        elif isinstance(expires_delta, int):
            exp = datetime.utcnow() + timedelta(minutes=expires_delta)
        else:
            exp = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        **data,
        "iat": datetime.utcnow(),
        "exp": exp,
        "jti": jti,
        "refresh": refresh,
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token, jti


def decode_jwt(token: str) -> Optional[Dict]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


# ---------------------------
# Async generator wrapper for middleware
# ---------------------------
@asynccontextmanager
async def get_db_session():
    async for session in get_db():
        yield session


# ---------------------------
# JWT Middleware
# ---------------------------
async def jwt_middleware(request: Request, call_next):
# In middleware
    if any(request.url.path.startswith(path) for path in PUBLIC_URLS):
        return await call_next(request)

    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return standard_response(
            success=False,
            message="Missing or invalid token",
            error="Unauthorized",
            status_code=status.HTTP_401_UNAUTHORIZED
        )

    token = auth_header.split(" ")[1]
    payload = decode_jwt(token)
    if not payload:
        return standard_response(
            success=False,
            message="Invalid or expired token",
            error="Unauthorized",
            status_code=status.HTTP_401_UNAUTHORIZED
        )

    jti = payload.get("jti")
    user_id = payload.get("sub")

    try:
        async with get_db_session() as db:
            # Check revoked token
            result = await db.execute(select(RevokedToken).where(RevokedToken.jti == jti))
            revoked = result.scalars().first()
            if revoked:
                return standard_response(
                    success=False,
                    message="Token has been revoked",
                    error="Unauthorized",
                    status_code=status.HTTP_401_UNAUTHORIZED
                )

            # Fetch user
            result = await db.execute(select(AuthUser).where(AuthUser.id == int(user_id)))
            user = result.scalars().first()
            if not user or not user.is_active:
                return standard_response(
                    success=False,
                    message="User not found or inactive",
                    error="Unauthorized",
                    status_code=status.HTTP_401_UNAUTHORIZED
                )

    except Exception as e:
        return standard_response(
            success=False,
            message="Unexpected error in middleware",
            error=str(e),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    # Attach user info to request.state
    request.state.user = {
        "id": user.id,
        "email": user.email,
        "db_user": user
    }

    return await call_next(request)


# ---------------------------
# Dependency for endpoints
# ---------------------------
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> AuthUser:
    payload = decode_jwt(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    jti = payload.get("jti")

    # 🔹 Check if token is revoked
    result = await db.execute(select(RevokedToken).where(RevokedToken.jti == jti))
    revoked = result.scalars().first()
    if revoked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
        )

    # 🔹 Fetch the current user
    user_id = payload.get("sub")
    result = await db.execute(select(AuthUser).where(AuthUser.id == int(user_id)))
    user = result.scalars().first()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    return user
