from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import get_settings
from app.core.database import init_db, close_db, get_db
from app.core.exceptions import (
    VoiceStudioError,
    voice_studio_exception_handler,
    validation_exception_handler,
    integrity_error_handler,
    sqlalchemy_error_handler,
    generic_exception_handler,
)
from app.api.router import api_router
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import text
from pydantic import ValidationError as PydanticValidationError

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting VoiceStudio...")
    await init_db()
    logger.info("Database initialized")
    yield
    logger.info("Shutting down VoiceStudio...")
    await close_db()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Open-source voice cloning, synthesis, and audio processing platform",
        lifespan=lifespan,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
    )

    # Session middleware for OIDC
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.secret_key,
        session_cookie="voicestudio_session",
        max_age=settings.access_token_expire_minutes * 60,
        same_site="lax",
        https_only=settings.environment == "production",
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception handlers
    app.add_exception_handler(VoiceStudioError, voice_studio_exception_handler)
    app.add_exception_handler(PydanticValidationError, validation_exception_handler)
    app.add_exception_handler(IntegrityError, integrity_error_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_error_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    # API routes
    app.include_router(api_router, prefix="/api")

    # Health check at root for load balancers
    @app.get("/")
    async def root():
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "status": "running",
            "docs": "/docs" if settings.debug else "disabled",
        }

    @app.get("/health")
    async def health_root(db: AsyncSession = Depends(get_db)):
        db_status = "ok"
        try:
            await db.execute(text("SELECT 1"))
        except Exception:
            db_status = "error"
        return {
            "status": "healthy" if db_status == "ok" else "degraded",
            "version": settings.app_version,
            "environment": settings.environment,
        }

    @app.get("/health/ready")
    async def readiness_root(db: AsyncSession = Depends(get_db)):
        try:
            await db.execute(text("SELECT 1"))
            return {"status": "ready"}
        except Exception:
            return {"status": "not ready"}

    # Static files for generated audio (development only)
    if settings.debug:
        from pathlib import Path
        upload_dir = Path(settings.upload_dir)
        upload_dir.mkdir(parents=True, exist_ok=True)
        app.mount("/files", StaticFiles(directory=str(upload_dir)), name="files")

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )