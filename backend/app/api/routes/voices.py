from typing import Annotated
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.api.deps import get_db, get_current_active_user, require_operator, require_admin, get_optional_user
from app.models import Voice, VoiceType, User, UserRole
from app.schemas import (
    VoiceCreate,
    VoiceUpdate,
    VoiceResponse,
    VoiceListResponse,
)
from app.core.exceptions import NotFoundError, InputValidationError

router = APIRouter(prefix="/voices", tags=["voices"])


@router.get("", response_model=VoiceListResponse)
async def list_voices(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    voice_type: VoiceType | None = None,
    language: str | None = None,
    is_active: bool | None = None,
    search: str | None = None,
):
    query = select(Voice)
    count_query = select(func.count(Voice.id))

    if voice_type:
        query = query.where(Voice.voice_type == voice_type)
        count_query = count_query.where(Voice.voice_type == voice_type)
    if language:
        query = query.where(Voice.language == language)
        count_query = count_query.where(Voice.language == language)
    if is_active is not None:
        query = query.where(Voice.is_active == (1 if is_active else 0))
        count_query = count_query.where(Voice.is_active == (1 if is_active else 0))
    if search:
        search_term = f"%{search}%"
        query = query.where(Voice.name.ilike(search_term) | Voice.description.ilike(search_term))
        count_query = count_query.where(Voice.name.ilike(search_term) | Voice.description.ilike(search_term))

    # Non-admin users only see their own cloned/designed voices + all builtin
    if current_user and not current_user.is_superuser and current_user.role != UserRole.ADMIN:
        from sqlalchemy import or_
        query = query.where(or_(Voice.voice_type == VoiceType.BUILTIN, Voice.owner_id == current_user.id))
        count_query = count_query.where(or_(Voice.voice_type == VoiceType.BUILTIN, Voice.owner_id == current_user.id))

    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    query = query.order_by(Voice.voice_type, Voice.name).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    voices = result.scalars().all()

    return VoiceListResponse(
        voices=[VoiceResponse.model_validate(v) for v in voices],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{voice_id}", response_model=VoiceResponse)
async def get_voice(
    voice_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    result = await db.execute(select(Voice).where(Voice.id == voice_id))
    voice = result.scalar_one_or_none()
    if not voice:
        raise NotFoundError("Voice", voice_id)

    # Check access
    if voice.voice_type != VoiceType.BUILTIN and voice.owner_id != current_user.id:
        if not current_user.is_superuser and current_user.role != UserRole.ADMIN:
            raise NotFoundError("Voice", voice_id)

    return VoiceResponse.model_validate(voice)


@router.post("", response_model=VoiceResponse, status_code=status.HTTP_201_CREATED)
async def create_voice(
    voice_data: VoiceCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_operator)],
):
    # Validate voice_type specific fields
    if voice_data.voice_type == VoiceType.CLONED and not voice_data.reference_audio_path:
        raise InputValidationError("Cloned voices require reference_audio_path")
    if voice_data.voice_type == VoiceType.DESIGNED and not voice_data.design_params:
        raise InputValidationError("Designed voices require design_params")

    voice = Voice(
        **voice_data.model_dump(),
        owner_id=current_user.id if voice_data.voice_type != VoiceType.BUILTIN else None,
        is_active=1,
    )
    db.add(voice)
    await db.commit()
    await db.refresh(voice)
    return VoiceResponse.model_validate(voice)


@router.patch("/{voice_id}", response_model=VoiceResponse)
async def update_voice(
    voice_id: int,
    voice_data: VoiceUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_operator)],
):
    result = await db.execute(select(Voice).where(Voice.id == voice_id))
    voice = result.scalar_one_or_none()
    if not voice:
        raise NotFoundError("Voice", voice_id)

    # Check ownership for non-builtin voices
    if voice.voice_type != VoiceType.BUILTIN and voice.owner_id != current_user.id:
        if not current_user.is_superuser and current_user.role != UserRole.ADMIN:
            raise NotFoundError("Voice", voice_id)

    update_data = voice_data.model_dump(exclude_unset=True)
    if "is_active" in update_data:
        update_data["is_active"] = 1 if update_data["is_active"] else 0

    for field, value in update_data.items():
        setattr(voice, field, value)

    await db.commit()
    await db.refresh(voice)
    return VoiceResponse.model_validate(voice)


@router.delete("/{voice_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_voice(
    voice_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_admin)],
):
    result = await db.execute(select(Voice).where(Voice.id == voice_id))
    voice = result.scalar_one_or_none()
    if not voice:
        raise NotFoundError("Voice", voice_id)

    if voice.voice_type == VoiceType.BUILTIN:
        raise InputValidationError("Cannot delete builtin voices")

    await db.delete(voice)
    await db.commit()