from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, model_validator
from enum import Enum


class VoiceType(str, Enum):
    BUILTIN = "builtin"
    CLONED = "cloned"
    DESIGNED = "designed"


class SynthesisStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class UserRole(str, Enum):
    VIEWER = "viewer"
    OPERATOR = "operator"
    ADMIN = "admin"


class VoiceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    language: str = Field(default="en", min_length=2, max_length=10)
    sample_rate: int = Field(default=22050, ge=8000, le=48000)


class VoiceCreate(VoiceBase):
    voice_type: VoiceType = VoiceType.BUILTIN
    model_id: Optional[str] = None
    reference_audio_path: Optional[str] = None
    design_params: Optional[str] = None

    model_config = ConfigDict(protected_namespaces=())

    @model_validator(mode="after")
    def validate_voice_type_fields(self):
        if self.voice_type == VoiceType.CLONED and not self.reference_audio_path:
            raise ValueError("Cloned voices require reference_audio_path")
        if self.voice_type == VoiceType.DESIGNED and not self.design_params:
            raise ValueError("Designed voices require design_params")
        return self


class VoiceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    language: Optional[str] = Field(None, min_length=2, max_length=10)
    is_active: Optional[bool] = None


class VoiceResponse(VoiceBase):
    id: int
    voice_type: VoiceType
    model_id: Optional[str] = None
    reference_audio_path: Optional[str] = None
    design_params: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    owner_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


class VoiceListResponse(BaseModel):
    voices: list[VoiceResponse]
    total: int
    page: int
    page_size: int


class SynthesisJobBase(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)
    voice_id: int = Field(..., gt=0)
    speed: int = Field(default=100, ge=50, le=200)
    pitch: int = Field(default=0, ge=-12, le=12)


class SynthesisJobCreate(SynthesisJobBase):
    pass


class SynthesisJobUpdate(BaseModel):
    status: Optional[SynthesisStatus] = None
    output_path: Optional[str] = None
    duration_seconds: Optional[int] = None
    error_message: Optional[str] = None


class SynthesisJobResponse(SynthesisJobBase):
    id: int
    status: SynthesisStatus
    output_path: Optional[str] = None
    duration_seconds: Optional[int] = None
    error_message: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    owner_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class SynthesisJobListResponse(BaseModel):
    jobs: list[SynthesisJobResponse]
    total: int
    page: int
    page_size: int


class UserBase(BaseModel):
    email: str = Field(..., pattern=r"^[^@]+@[^@]+\.[^@]+$|^[^@]+@localhost$")
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    full_name: Optional[str] = None
    role: UserRole = UserRole.VIEWER


class UserCreate(UserBase):
    password: Optional[str] = Field(None, min_length=8, max_length=128)


class UserUpdate(BaseModel):
    email: Optional[str] = Field(None, pattern=r"^[^@]+@[^@]+\.[^@]+$")
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    id: int
    is_active: bool
    is_superuser: bool
    oidc_sub: Optional[str] = None
    oidc_provider: Optional[str] = None
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str