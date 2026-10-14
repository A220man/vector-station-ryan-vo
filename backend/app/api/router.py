from fastapi import APIRouter

from app.api.routes import health, voices, synthesis, auth

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(voices.router)
api_router.include_router(synthesis.router)
api_router.include_router(auth.router)