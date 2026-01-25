from pydantic import BaseModel, EmailStr, constr,Field

class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class TokenResetPasswordRequest(BaseModel):
    new_password: str = Field(...)
    confirm_password: str = Field(...)

class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp: int
class PasswordResetSchema(BaseModel):
    token: str = Field(...)
    new_password: str = Field(...)
    confirm_password: str = Field(...)
    
class ResetPasswordRequest(BaseModel):
    email: EmailStr
    new_password: str = Field(...)
    confirm_password: str = Field(...)
   