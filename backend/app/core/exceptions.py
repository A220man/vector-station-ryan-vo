from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
import logging

logger = logging.getLogger(__name__)


class VoiceStudioError(Exception):
    def __init__(self, message: str, code: str = "INTERNAL_ERROR", details: dict | None = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(message)


class NotFoundError(VoiceStudioError):
    def __init__(self, resource: str, identifier: str | int):
        super().__init__(
            message=f"{resource} not found: {identifier}",
            code="NOT_FOUND",
            details={"resource": resource, "identifier": str(identifier)},
        )


class InputValidationError(VoiceStudioError):
    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message=message, code="VALIDATION_ERROR", details=details)


class AuthenticationError(VoiceStudioError):
    def __init__(self, message: str = "Authentication required"):
        super().__init__(message=message, code="AUTHENTICATION_ERROR")


class AuthorizationError(VoiceStudioError):
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message=message, code="AUTHORIZATION_ERROR")


class SynthesisError(VoiceStudioError):
    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message=message, code="SYNTHESIS_ERROR", details=details)


async def voice_studio_exception_handler(request: Request, exc: VoiceStudioError) -> JSONResponse:
    logger.warning(f"VoiceStudioError: {exc.code} - {exc.message}", extra=exc.details)
    status_code_map = {
        "NOT_FOUND": status.HTTP_404_NOT_FOUND,
        "VALIDATION_ERROR": status.HTTP_422_UNPROCESSABLE_ENTITY,
        "AUTHENTICATION_ERROR": status.HTTP_401_UNAUTHORIZED,
        "AUTHORIZATION_ERROR": status.HTTP_403_FORBIDDEN,
        "SYNTHESIS_ERROR": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "INTERNAL_ERROR": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "INTEGRITY_ERROR": status.HTTP_409_CONFLICT,
        "DATABASE_ERROR": status.HTTP_500_INTERNAL_SERVER_ERROR,
    }
    return JSONResponse(
        status_code=status_code_map.get(exc.code, status.HTTP_400_BAD_REQUEST),
        content={"code": exc.code, "message": exc.message, "details": exc.details},
    )


async def validation_exception_handler(request: Request, exc: PydanticValidationError) -> JSONResponse:
    logger.warning(f"Validation error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "code": "VALIDATION_ERROR",
            "message": "Invalid request data",
            "details": {"errors": exc.errors()},
        },
    )


async def integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
    logger.error(f"Database integrity error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"code": "INTEGRITY_ERROR", "message": "Database integrity error", "details": {}},
    )


async def sqlalchemy_error_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    logger.error(f"Database error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"code": "DATABASE_ERROR", "message": "Database error", "details": {}},
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"code": "INTERNAL_ERROR", "message": "Internal server error", "details": {}},
    )