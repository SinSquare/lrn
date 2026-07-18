"""Error classes and handlers."""

import logging

from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import HTTPException, RequestValidationError
from pydantic import BaseModel, Field
from starlette.responses import JSONResponse

log = logging.getLogger(__name__)


class ApiException(HTTPException):
    """HTTP exception base class."""

    status_code: int

    def __init__(
        self, message=None, headers=None, details=None, status_code: int = None
    ):
        """Init HTTPException with status code 403."""
        sc = 500
        if getattr(self, "status_code", None):
            sc = self.status_code
        elif status_code:
            sc = status_code
        self.status_code = sc
        super().__init__(status_code=self.status_code, detail=message, headers=headers)
        self.details = details

    @property
    def message(self) -> str:
        """Return exception detail as message."""
        return self.detail

    def __str__(self) -> str:
        """Return string representation."""
        return self.message


class BadRequest(ApiException):
    """400 BadRequest."""

    status_code = 400


class Unauthorized(ApiException):
    """401 Unauthorized."""

    status_code = 401


class Forbidden(ApiException):
    """403 Forbidden."""

    status_code = 403


class NotFound(ApiException):
    """404 Not Found."""

    status_code = 404


class Conflict(ApiException):
    """409 Conflict."""

    status_code = 409


class Unprocessable(ApiException):
    """422 Unprocessable Entity."""

    status_code = 422


def http_exc_handler(_, exc: HTTPException) -> JSONResponse:
    """Return JSON with message field (instead of detail) on HTTPException."""
    log.error(f"HTTP error {type(exc).__name__}: {exc}", exc_info=exc)
    content = {"message": exc.detail}
    if details := getattr(exc, "details", None):
        content["details"] = jsonable_encoder(details, exclude_none=True)
    return JSONResponse(
        content,
        status_code=exc.status_code,
        headers=getattr(exc, "headers", None),
    )


def request_validation_exc_handler(_, exc: RequestValidationError) -> JSONResponse:
    """Return JSON with message field (instead of pydantic objects)."""
    return http_exc_handler(_, BadRequest(str(exc)))


def exc_handler(_, exc: Exception) -> JSONResponse:
    """Return JSON with internal server error message on all unhandled Exception."""
    log.error(err := f"Unhandled {type(exc).__name__}: {exc}", exc_info=exc)
    return JSONResponse({"message": f"Internal Server Error: {err}"}, status_code=500)


handlers = {
    HTTPException: http_exc_handler,
    RequestValidationError: request_validation_exc_handler,
    Exception: exc_handler,
}


class ErrorResponse(BaseModel):
    """Error response schema."""

    message: str = Field(description="Error message")
    details: dict | None = Field(description="Error details")


responses = {
    400: {"model": ErrorResponse, "description": "Bad request"},
    401: {"model": ErrorResponse, "description": "Not authenticated"},
    403: {"model": ErrorResponse, "description": "Not authorized"},
    404: {"model": ErrorResponse, "description": "Not found"},
    409: {"model": ErrorResponse, "description": "Conflict"},
    422: {"model": ErrorResponse, "description": "Unprocessable"},
}
