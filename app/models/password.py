from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from app.core.db import Base


class PasswordOTP(Base):
    __tablename__ = "password_otp"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, nullable=False)
    otp = Column(Integer, nullable=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, default=lambda: datetime.utcnow() + timedelta(minutes=10))
    type = Column(String, default="otp") 