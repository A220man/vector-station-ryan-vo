from datetime import datetime, timezone
from enum import Enum as PyEnum
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    Enum as SQLEnum,
    Index,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship, declarative_mixin

from app.core.database import Base


class VoiceType(PyEnum):
    BUILTIN = "builtin"
    CLONED = "cloned"
    DESIGNED = "designed"


class SynthesisStatus(PyEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class UserRole(PyEnum):
    VIEWER = "viewer"
    OPERATOR = "operator"
    ADMIN = "admin"


class Voice(Base):
    __tablename__ = "voices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    voice_type = Column(SQLEnum(VoiceType, values_callable=lambda x: [e.value for e in x]), nullable=False, default=VoiceType.BUILTIN)
    language = Column(String(10), nullable=False, default="en")
    sample_rate = Column(Integer, nullable=False, default=22050)
    # For cloned voices: path to reference audio or embedding
    reference_audio_path = Column(String(512), nullable=True)
    # For designed voices: JSON parameters
    design_params = Column(Text, nullable=True)  # JSON string
    # For builtin voices: model identifier
    model_id = Column(String(255), nullable=True)
    is_active = Column(Integer, nullable=False, default=1)  # SQLite bool
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    owner = relationship("User", back_populates="voices")
    syntheses = relationship("SynthesisJob", back_populates="voice")

    __table_args__ = (
        Index("ix_voices_type_active", "voice_type", "is_active"),
        Index("ix_voices_owner", "owner_id"),
    )


class SynthesisJob(Base):
    __tablename__ = "synthesis_jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    text = Column(Text, nullable=False)
    voice_id = Column(Integer, ForeignKey("voices.id"), nullable=False)
    status = Column(SQLEnum(SynthesisStatus, values_callable=lambda x: [e.value for e in x]), nullable=False, default=SynthesisStatus.PENDING)
    output_path = Column(String(512), nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    # Synthesis parameters
    speed = Column(Integer, nullable=False, default=100)  # percentage
    pitch = Column(Integer, nullable=False, default=0)  # semitones
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    voice = relationship("Voice", back_populates="syntheses")
    owner = relationship("User", back_populates="syntheses")

    __table_args__ = (
        Index("ix_synthesis_status", "status"),
        Index("ix_synthesis_owner", "owner_id"),
        Index("ix_synthesis_voice", "voice_id"),
    )


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=True, index=True)
    hashed_password = Column(String(255), nullable=True)  # Nullable for OIDC-only users
    full_name = Column(String(255), nullable=True)
    role = Column(SQLEnum(UserRole, values_callable=lambda x: [e.value for e in x]), nullable=False, default=UserRole.VIEWER)
    is_active = Column(Integer, nullable=False, default=1)
    is_superuser = Column(Integer, nullable=False, default=0)
    # OIDC fields
    oidc_sub = Column(String(255), unique=True, nullable=True, index=True)
    oidc_provider = Column(String(100), nullable=True)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    voices = relationship("Voice", back_populates="owner")
    syntheses = relationship("SynthesisJob", back_populates="owner")

    __table_args__ = (
        UniqueConstraint("email", name="uq_users_email"),
        UniqueConstraint("username", name="uq_users_username"),
        UniqueConstraint("oidc_sub", name="uq_users_oidc_sub"),
    )