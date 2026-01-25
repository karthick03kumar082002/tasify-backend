from sqlalchemy import Column, ForeignKey, Integer, String, Boolean, DateTime, Text, Date
from app.core.db import Base
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship


class AuthUser(Base):
    __tablename__ = "auth_user"
   
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String,  index=True, nullable=False)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    dob = Column(Date, nullable=True)
    age = Column(Integer, index=True, nullable=True)
    gender = Column(String,nullable=True)
    email = Column(String, nullable=False)
    phone_number = Column(String,  nullable=True)
    password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    profile_image = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    boards = relationship(
        "Board",
        back_populates="user",
        cascade="all, delete-orphan"
    )

class RevokedToken(Base):
    __tablename__ = "revoked_tokens"
    jti = Column(String, primary_key=True, index=True)
    revoked_at = Column(DateTime, default=datetime.utcnow)