from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import Voice, VoiceType, User, UserRole
from app.core.security import get_password_hash
from app.core.config import get_settings


async def create_builtin_voices(db: AsyncSession) -> None:
    """Create default builtin voices."""
    builtin_voices = [
        {
            "name": "Default Female",
            "description": "Default female voice for English",
            "voice_type": VoiceType.BUILTIN,
            "language": "en",
            "sample_rate": 22050,
            "model_id": "default_female",
            "is_active": 1,
        },
        {
            "name": "Default Male",
            "description": "Default male voice for English",
            "voice_type": VoiceType.BUILTIN,
            "language": "en",
            "sample_rate": 22050,
            "model_id": "default_male",
            "is_active": 1,
        },
        {
            "name": "Narrator",
            "description": "Neutral narrator voice for audiobooks",
            "voice_type": VoiceType.BUILTIN,
            "language": "en",
            "sample_rate": 22050,
            "model_id": "narrator",
            "is_active": 1,
        },
    ]

    for voice_data in builtin_voices:
        result = await db.execute(
            select(Voice).where(Voice.model_id == voice_data["model_id"])
        )
        existing = result.scalar_one_or_none()
        if not existing:
            voice = Voice(**voice_data)
            db.add(voice)

    await db.commit()


async def create_dev_user(db: AsyncSession) -> None:
    """Create development user."""
    settings = get_settings()
    if settings.environment != "development":
        return

    result = await db.execute(select(User).where(User.username == "dev"))
    existing = result.scalar_one_or_none()
    if not existing:
        user = User(
            email="dev@localhost",
            username="dev",
            hashed_password=get_password_hash("dev"),
            full_name="Development User",
            role=UserRole.ADMIN,
            is_active=True,
            is_superuser=True,
        )
        db.add(user)
        await db.commit()


async def init_data(db: AsyncSession) -> None:
    await create_builtin_voices(db)
    await create_dev_user(db)