# Copyright (C) 2023 Canonical Ltd.
#
# This file is part of Test Observer Backend.
#
# Test Observer Backend is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License version 3, as
# published by the Free Software Foundation.
#
# Test Observer Backend is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


import logging
import traceback
import uuid
from typing import Any, Dict, Optional

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

logger = logging.getLogger(__name__)


class ErrorDetail(BaseModel):
    """Structured error detail model"""
    type: str = Field(..., description="Error type identifier")
    message: str = Field(..., description="Human-readable error message")
    code: str = Field(..., description="Unique error code for this incident")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error context")


class ErrorResponse(BaseModel):
    """Standard error response format"""
    error: ErrorDetail
    debug_info: Optional[Dict[str, Any]] = Field(None, description="Debug information (development only)")


class BusinessLogicError(Exception):
    """Custom exception for business logic errors"""
    def __init__(
        self,
        message: str,
        error_type: str = "business_logic_error",
        details: Optional[Dict[str, Any]] = None,
        status_code: int = status.HTTP_400_BAD_REQUEST
    ):
        self.message = message
        self.error_type = error_type
        self.details = details or {}
        self.status_code = status_code
        super().__init__(message)


class ValidationError(Exception):
    """Custom exception for validation errors"""
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.field = field
        self.value = value
        self.details = details or {}
        if field:
            self.details["field"] = field
        if value is not None:
            self.details["invalid_value"] = value
        super().__init__(message)


class DatabaseError(Exception):
    """Custom exception for database-related errors"""
    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.operation = operation
        self.details = details or {}
        if operation:
            self.details["operation"] = operation
        super().__init__(message)


def generate_error_code() -> str:
    """Generate a unique error code for tracking"""
    return str(uuid.uuid4())[:8].upper()


def create_error_response(
    error_type: str,
    message: str,
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    details: Optional[Dict[str, Any]] = None,
    include_debug: bool = False,
    exception: Optional[Exception] = None
) -> JSONResponse:
    """Create a standardized error response"""
    error_code = generate_error_code()
    
    error_detail = ErrorDetail(
        type=error_type,
        message=message,
        code=error_code,
        details=details
    )
    
    response_data = {"error": error_detail.model_dump()}
    
    # Add debug information in development
    if include_debug and exception:
        response_data["debug_info"] = {
            "exception_type": type(exception).__name__,
            "exception_message": str(exception),
            "traceback": traceback.format_exc().split('\n')[-10:]  # Last 10 lines only
        }
    
    # Log the error with full context
    logger.error(
        f"Error {error_code}: {error_type} - {message}",
        extra={
            "error_code": error_code,
            "error_type": error_type,
            "status_code": status_code,
            "details": details,
            "exception": str(exception) if exception else None
        },
        exc_info=exception is not None
    )
    
    return JSONResponse(
        status_code=status_code,
        content=response_data
    )


async def business_logic_exception_handler(request: Request, exc: BusinessLogicError) -> JSONResponse:
    """Handle business logic errors"""
    return create_error_response(
        error_type=exc.error_type,
        message=exc.message,
        status_code=exc.status_code,
        details=exc.details,
        include_debug=should_include_debug(request),
        exception=exc
    )


async def validation_exception_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """Handle validation errors"""
    return create_error_response(
        error_type="validation_error",
        message=exc.message,
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        details=exc.details,
        include_debug=should_include_debug(request),
        exception=exc
    )


async def database_exception_handler(request: Request, exc: DatabaseError) -> JSONResponse:
    """Handle database errors"""
    return create_error_response(
        error_type="database_error",
        message=exc.message,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        details=exc.details,
        include_debug=should_include_debug(request),
        exception=exc
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """Handle SQLAlchemy errors"""
    if isinstance(exc, IntegrityError):
        message = "Data integrity constraint violation"
        error_type = "integrity_error"
        status_code = status.HTTP_409_CONFLICT
    else:
        message = "Database operation failed"
        error_type = "database_error"
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    
    return create_error_response(
        error_type=error_type,
        message=message,
        status_code=status_code,
        details={"database_error": True},
        include_debug=should_include_debug(request),
        exception=exc
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle FastAPI HTTPExceptions with enhanced formatting"""
    # Determine error type based on status code
    error_type_map = {
        400: "bad_request",
        401: "unauthorized",
        403: "forbidden",
        404: "not_found",
        409: "conflict",
        422: "validation_error",
        500: "internal_error"
    }
    
    error_type = error_type_map.get(exc.status_code, "http_error")
    
    return create_error_response(
        error_type=error_type,
        message=exc.detail if isinstance(exc.detail, str) else "An error occurred",
        status_code=exc.status_code,
        details={"http_status": exc.status_code},
        include_debug=should_include_debug(request),
        exception=exc
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions"""
    return create_error_response(
        error_type="internal_error",
        message="An unexpected error occurred. Please try again later.",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        details={"unexpected_error": True},
        include_debug=should_include_debug(request),
        exception=exc
    )


def should_include_debug(request: Request) -> bool:
    """Determine if debug information should be included based on environment"""
    # Check for debug header or query parameter
    debug_header = request.headers.get("X-Debug-Errors", "").lower()
    debug_query = request.query_params.get("debug", "").lower()
    
    return debug_header in ("1", "true") or debug_query in ("1", "true")


def setup_error_handlers(app):
    """Setup all error handlers for the FastAPI app"""
    app.add_exception_handler(BusinessLogicError, business_logic_exception_handler)
    app.add_exception_handler(ValidationError, validation_exception_handler)
    app.add_exception_handler(DatabaseError, database_exception_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)