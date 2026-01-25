from fastapi import Request, status
from sqlalchemy.future import select
from passlib.context import CryptContext
from app.models.users import AuthUser,RevokedToken
from app.core.response import AppException
from app.utils.jwt import create_jwt, decode_jwt
from sqlalchemy.exc import IntegrityError
from app.schema.login_schema import RefreshTokenRequest
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    def __init__(self, db):
        self.db = db

    async def login(self, email: str, password: str, request: Request):
        # --------------------------
        #  Check user exists
        # --------------------------
        user = (
            await self.db.execute(select(AuthUser).where(AuthUser.email == email))
        ).scalars().first()

        if not user:
            raise AppException(
                message="Email Not Found",
                error="Unauthorized",
                status_code=status.HTTP_401_UNAUTHORIZED
            )

        # --------------------------
        #  Verify password
        # --------------------------
        if not pwd_context.verify(password, user.password):
            raise AppException(
                message="Invalid password",
                error="Unauthorized",
                status_code=status.HTTP_401_UNAUTHORIZED
            )

        # --------------------------
        #  Check if user is active
        # --------------------------
        if not user.is_active:
            raise AppException(
                message="Your account is inactive",
                error="InactiveUser",
                status_code=status.HTTP_403_FORBIDDEN
            )

        # --------------------------
        #  Generate JWT tokens
        # --------------------------
        claims = {
            "sub": str(user.id),
            "email": user.email,
        }

        access_token, _ = create_jwt(claims)
        refresh_token, _ = create_jwt(claims, refresh=True)

        # --------------------------
        # response
        # --------------------------
        return {
            "success": True,
            "message": "Login successful",
            "data": {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "user_id": user.id,
                "email": user.email,
            },
            "error": None,
        }
    async def logout(self, request: Request):
    
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer"):
                raise AppException(
                    message="Missing token",
                    error="Unauthorized",
                    status_code=status.HTTP_401_UNAUTHORIZED
                )

            token = auth_header.split(" ")[1]
            payload = decode_jwt(token)
            if not payload:
                raise AppException(
                    message="Invalid or expired token",
                    error="Unauthorized",
                    status_code=status.HTTP_401_UNAUTHORIZED
                )

            jti = payload.get("jti")
            # Check if token is already revoked
            result = await self.db.execute(select(RevokedToken).where(RevokedToken.jti == jti))
            existing = result.scalars().first()
            if existing:
                raise AppException(
                    message="Token is already revoked",
                    error="Token blocklisted",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            # Revoke the token
            revoked_token = RevokedToken(jti=jti)
            self.db.add(revoked_token)
            try:
                await self.db.commit()
            except IntegrityError:
                await self.db.rollback()
                raise AppException(
                    message="Token is already revoked",
                    error="Token blocklisted",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            return {
                "success": True,
                "message": "Token revoked successfully",
                "data": None,
                "error": None,
            }
    
    async def refresh_access_token(self, payload: RefreshTokenRequest):
        refresh_token = payload.refresh_token
        if not refresh_token:
            raise AppException(
                message="Missing refresh token",
                error="Unauthorized",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        # Decode the refresh token
        token_data = decode_jwt(refresh_token)
        if not token_data:
            raise AppException(
                message="Invalid or expired refresh token",
                error="Unauthorized",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        jti = token_data.get("jti")
        # Check if token is revoked
        result = await self.db.execute(
            select(RevokedToken).where(RevokedToken.jti == jti)
        )
        if result.scalars().first():
            raise AppException(
                message="Refresh token is revoked",
                error="Unauthorized",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        # Generate new access token
        claims = {
            "sub": token_data.get("sub"),
            "email": token_data.get("email"),
        }
        access_token, _ = create_jwt(claims)

        return {
            "success": True,
            "message": "Access token refreshed",
            "data": {
                "access_token": access_token,
                "token_type": "bearer",
            },
            "error": None,
        }
