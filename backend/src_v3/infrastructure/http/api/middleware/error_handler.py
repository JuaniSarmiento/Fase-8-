"""
Error handling middleware
"""
import logging
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.src_v3.core.domain.exceptions import (
    DomainException,
    EntityNotFoundException,
    ValidationException,
    BusinessRuleViolationException
)

logger = logging.getLogger(__name__)


async def domain_exception_handler(request: Request, exc: DomainException) -> JSONResponse:
    """
    Handle domain exceptions.
    
    Translates domain exceptions to HTTP responses.
    """
    logger.warning(f"Domain exception: {exc}", exc_info=True)
    
    if isinstance(exc, EntityNotFoundException):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": "not_found",
                "message": str(exc),
                "entity_type": exc.entity_type,
                "entity_id": exc.entity_id
            }
        )
    
    if isinstance(exc, ValidationException):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": "validation_error",
                "message": str(exc)
            }
        )
    
    if isinstance(exc, BusinessRuleViolationException):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "business_rule_violation",
                "message": str(exc)
            }
        )
    
    # Generic domain exception
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "domain_error",
            "message": str(exc)
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Handle Pydantic validation errors.
    """
    logger.warning(f"Validation error: {exc.errors()}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "validation_error",
            "message": "Invalid request data",
            "details": exc.errors()
        }
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """
    Handle HTTP exceptions.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "http_error",
            "message": exc.detail
        }
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle unexpected exceptions.
    """
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "internal_server_error",
            "message": "An unexpected error occurred"
        }
    )
