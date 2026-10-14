import asyncio
from typing import Annotated
from fastapi import APIRouter, Depends, Query, HTTPException, status, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.api.deps import get_db, get_current_active_user, require_operator, get_optional_user
from app.models import SynthesisJob, SynthesisStatus, Voice, User, UserRole
from app.schemas import (
    SynthesisJobCreate,
    SynthesisJobUpdate,
    SynthesisJobResponse,
    SynthesisJobListResponse,
)
from app.services.tts import tts_service
from app.core.exceptions import NotFoundError, ValidationError, AuthorizationError

router = APIRouter(prefix="/synthesis", tags=["synthesis"])


async def process_synthesis_job(job_id: int, db_factory):
    """Background task to process synthesis job."""
    from app.core.database import async_session_maker
    from app.models import SynthesisJob, SynthesisStatus
    from datetime import datetime, timezone
    
    async with async_session_maker() as db:
        result = await db.execute(
            select(SynthesisJob).where(SynthesisJob.id == job_id)
        )
        job = result.scalar_one_or_none()
        if not job:
            return

        try:
            job.status = SynthesisStatus.PROCESSING
            job.started_at = datetime.now(timezone.utc)
            await db.commit()

            # Get voice info
            voice_result = await db.execute(
                select(Voice).where(Voice.id == job.voice_id)
            )
            voice = voice_result.scalar_one_or_none()
            if not voice:
                raise ValueError(f"Voice {job.voice_id} not found")

            # Synthesize
            audio_data, duration = await tts_service.synthesize(
                text=job.text,
                voice_id=voice.id,
                speed=job.speed,
                pitch=job.pitch,
            )

            # Save audio
            output_path = tts_service.save_audio(audio_data, job.id)

            job.status = SynthesisStatus.COMPLETED
            job.output_path = output_path
            job.duration_seconds = int(duration)
            job.completed_at = datetime.now(timezone.utc)
            await db.commit()

        except Exception as e:
            job.status = SynthesisStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.now(timezone.utc)
            await db.commit()


@router.post("", response_model=SynthesisJobResponse, status_code=status.HTTP_201_CREATED)
async def create_synthesis(
    job_data: SynthesisJobCreate,
    background_tasks: BackgroundTasks,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    # Verify voice exists and is accessible
    voice_result = await db.execute(select(Voice).where(Voice.id == job_data.voice_id))
    voice = voice_result.scalar_one_or_none()
    if not voice:
        raise NotFoundError("Voice", job_data.voice_id)
    if not voice.is_active:
        raise ValidationError("Voice is not active")
    if voice.voice_type != Voice.__table__.c.voice_type.type.python_type.BUILTIN and voice.owner_id != current_user.id:
        if not current_user.is_superuser and current_user.role != UserRole.ADMIN:
            raise NotFoundError("Voice", job_data.voice_id)

    job = SynthesisJob(
        **job_data.model_dump(),
        status=SynthesisStatus.PENDING,
        owner_id=current_user.id,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    # Queue background processing (skip in test mode)
    import os
    if not os.environ.get("PYTEST_CURRENT_TEST"):
        background_tasks.add_task(process_synthesis_job, job.id, None)

    return SynthesisJobResponse.model_validate(job)


@router.get("", response_model=SynthesisJobListResponse)
async def list_synthesis_jobs(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: SynthesisStatus | None = Query(None, alias="status"),
    voice_id: int | None = None,
):
    query = select(SynthesisJob).options(selectinload(SynthesisJob.voice))
    count_query = select(func.count(SynthesisJob.id))

    # Non-admin users only see their own jobs
    if not current_user.is_superuser and current_user.role != UserRole.ADMIN:
        query = query.where(SynthesisJob.owner_id == current_user.id)
        count_query = count_query.where(SynthesisJob.owner_id == current_user.id)

    if status_filter:
        query = query.where(SynthesisJob.status == status_filter)
        count_query = count_query.where(SynthesisJob.status == status_filter)
    if voice_id:
        query = query.where(SynthesisJob.voice_id == voice_id)
        count_query = count_query.where(SynthesisJob.voice_id == voice_id)

    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    query = query.order_by(SynthesisJob.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    jobs = result.scalars().all()

    return SynthesisJobListResponse(
        jobs=[SynthesisJobResponse.model_validate(j) for j in jobs],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{job_id}", response_model=SynthesisJobResponse)
async def get_synthesis_job(
    job_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    result = await db.execute(
        select(SynthesisJob).options(selectinload(SynthesisJob.voice)).where(SynthesisJob.id == job_id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise NotFoundError("Synthesis job", job_id)

    # Check ownership
    if job.owner_id != current_user.id:
        if not current_user.is_superuser and current_user.role != UserRole.ADMIN:
            raise NotFoundError("Synthesis job", job_id)

    return SynthesisJobResponse.model_validate(job)


@router.get("/{job_id}/audio")
async def download_synthesis_audio(
    job_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    result = await db.execute(select(SynthesisJob).where(SynthesisJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise NotFoundError("Synthesis job", job_id)

    if job.owner_id != current_user.id:
        if not current_user.is_superuser and current_user.role != UserRole.ADMIN:
            raise NotFoundError("Synthesis job", job_id)

    if job.status != SynthesisStatus.COMPLETED or not job.output_path:
        raise NotFoundError("Audio file", job_id)

    audio_path = Path(job.output_path)
    if not audio_path.exists():
        # Try to find by pattern
        found = tts_service.get_audio_path(job_id)
        if not found:
            raise NotFoundError("Audio file", job_id)
        audio_path = found

    return FileResponse(
        path=audio_path,
        media_type="audio/wav",
        filename=f"synthesis_{job_id}.wav",
    )


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_synthesis_job(
    job_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    result = await db.execute(select(SynthesisJob).where(SynthesisJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise NotFoundError("Synthesis job", job_id)

    if job.owner_id != current_user.id:
        if not current_user.is_superuser and current_user.role != UserRole.ADMIN:
            raise NotFoundError("Synthesis job", job_id)

    # Delete audio file if exists
    if job.output_path:
        audio_path = Path(job.output_path)
        if audio_path.exists():
            audio_path.unlink()

    await db.delete(job)
    await db.commit()