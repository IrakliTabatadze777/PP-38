import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.services.errors import (
    Conflict,
    Forbidden,
    InvalidInput,
    NotAuthenticated,
    NotFound,
    OutOfRange,
    ServiceError,
    TooLarge,
    Unavailable,
)

STATUS_FOR_ERROR: dict[type[ServiceError], int] = {
    NotAuthenticated: 401,
    Forbidden: 403,
    NotFound: 404,
    Conflict: 409,
    InvalidInput: 422,
    OutOfRange: 400,
    TooLarge: 413,
    Unavailable: 503,
}


class ApiError(Exception):
    def __init__(
        self, status_code: int, code: str, message: str, headers: dict[str, str] | None = None
    ) -> None:
        super().__init__(code)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.headers = headers


logger = logging.getLogger(__name__)


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def handle_api_error(_: Request, exc: ApiError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"code": exc.code, "message": exc.message},
            headers=exc.headers,
        )

    @app.exception_handler(ServiceError)
    async def handle_service_error(_: Request, exc: ServiceError) -> JSONResponse:
        headers = {"WWW-Authenticate": "Bearer"} if isinstance(exc, NotAuthenticated) else None
        return JSONResponse(
            status_code=STATUS_FOR_ERROR[type(exc)],
            content={"code": exc.code, "message": exc.message},
            headers=headers,
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        logger.error(
            "Unhandled error",
            exc_info=exc,
            extra={"event": "unhandled_error", "path": request.url.path},
        )
        return JSONResponse(
            status_code=500,
            content={
                "code": "internal_error",
                "message": "Something went wrong. Please try again.",
            },
        )
