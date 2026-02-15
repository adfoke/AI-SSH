from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from .db import Base


class Host(Base):
    __tablename__ = "hosts"
    __table_args__ = (
        CheckConstraint("auth_type IN ('key','password')", name="ck_hosts_auth_type"),
    )

    id = Column(Integer, primary_key=True)
    alias = Column(String, nullable=False)
    hostname = Column(String, nullable=False)
    port = Column(Integer, default=22)
    username = Column(String, nullable=False)
    auth_type = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    credentials = relationship("Credential", back_populates="host", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="host", cascade="all, delete-orphan")


class Credential(Base):
    __tablename__ = "credentials"
    __table_args__ = (
        CheckConstraint("auth_type IN ('key','password')", name="ck_credentials_auth_type"),
    )

    id = Column(Integer, primary_key=True)
    host_id = Column(Integer, ForeignKey("hosts.id"))
    auth_type = Column(String, nullable=False)
    encrypted_key_path = Column(Text)
    encrypted_password = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

    host = relationship("Host", back_populates="credentials")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)
    host_id = Column(Integer, ForeignKey("hosts.id"))
    user_query = Column(Text)
    ai_command = Column(Text)
    exit_code = Column(Integer)
    output = Column(Text)
    executed_at = Column(DateTime, server_default=func.now())

    host = relationship("Host", back_populates="audit_logs")
