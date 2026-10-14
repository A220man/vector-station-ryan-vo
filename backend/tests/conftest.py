import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.main import create_app
from app.core.database import Base, get_db
from app.models import User, UserRole, Voice, VoiceType, SynthesisJob, SynthesisStatus
from app.core.security import get_password_hash, create_access_token


# Test database - use file-based SQLite for proper table persistence across connections
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_voicestudio.db"
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    poolclass=NullPool,
    connect_args={"check_same_thread": False},
)

TestAsyncSessionMaker = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def override_get_db():
    async with TestAsyncSessionMaker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@pytest_asyncio.fixture(scope="function")
async def db_session():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestAsyncSessionMaker() as session:
        yield session
    
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db_session):
    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def dev_user(db_session):
    # Use a short password that bcrypt can handle (max 72 bytes)
    user = User(
        email="dev@localhost",
        username="dev",
        hashed_password=get_password_hash("dev"),
        full_name="Development User",
        role=UserRole.ADMIN,
        is_active=True,
        is_superuser=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def auth_headers(dev_user):
    token = create_access_token(subject=str(dev_user.id), roles=[dev_user.role.value])
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def builtin_voice(db_session):
    voice = Voice(
        name="Test Voice",
        description="A test voice",
        voice_type=VoiceType.BUILTIN,
        language="en",
        sample_rate=22050,
        model_id="test_voice",
        is_active=1,
    )
    db_session.add(voice)
    await db_session.commit()
    await db_session.refresh(voice)
    return voice