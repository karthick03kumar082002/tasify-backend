from sqlalchemy import Column, Integer, String, DateTime , ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.db import Base




class LoginAuditLog(Base):
    __tablename__ = "login_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True)  # nullable for failed login if user not found
    action = Column(String(50), nullable=False)  # login/logout/admin_login
    status = Column(String(20), nullable=False)  # "success" or "failure"
    ip_address = Column(String(45))
    user_agent = Column(String(255))
    message = Column(String(255), nullable=True)  # optional extra info
    timestamp = Column(DateTime, default=datetime.utcnow)



class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    table_name = Column(String, nullable=False)
    record_id = Column(Integer, nullable=True)
    action = Column(String, nullable=False)  # INSERT, UPDATE, DELETE
    changed_data = Column(JSON, nullable=True)
    user_id = Column(Integer, ForeignKey("auth_user.id",ondelete="SET NULL"),nullable=True)
    ip_address = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("AuthUser", backref="audit_logs")
