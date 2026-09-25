import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

Json = JSON().with_variant(JSONB, "postgresql")
def now(): return datetime.now(timezone.utc)
class Base(DeclarativeBase): pass
class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
class Endpoint(Base):
    __tablename__ = "endpoints"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True, nullable=True)
    name: Mapped[str] = mapped_column(String(100))
    token: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    max_body_size: Mapped[int] = mapped_column(Integer, default=1_048_576)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    requests: Mapped[list["CapturedRequest"]] = relationship(back_populates="endpoint", cascade="all, delete-orphan")
class CapturedRequest(Base):
    __tablename__ = "captured_requests"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    endpoint_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("endpoints.id"), index=True)
    method: Mapped[str] = mapped_column(String(10), index=True)
    path: Mapped[str] = mapped_column(String(2048))
    query: Mapped[dict] = mapped_column(Json, default=dict)
    headers: Mapped[dict] = mapped_column(Json, default=dict)
    cookies: Mapped[dict] = mapped_column(Json, default=dict)
    content_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    body_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    body_preview: Mapped[str | None] = mapped_column(Text, nullable=True)
    body_size: Mapped[int] = mapped_column(Integer)
    source_ip: Mapped[str] = mapped_column(String(64), index=True)
    user_agent: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    protocol: Mapped[str] = mapped_column(String(20))
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, index=True)
    endpoint: Mapped[Endpoint] = relationship(back_populates="requests")
class Replay(Base):
    __tablename__ = "replays"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("captured_requests.id"), index=True)
    target_url: Mapped[str] = mapped_column(String(2048))
    status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    response_headers: Mapped[dict | None] = mapped_column(Json, nullable=True)
    response_body: Mapped[str | None] = mapped_column(Text, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
