from starlette.responses import JSONResponse

from .exceptions import AppError, ForbiddenError, UnauthorizedError
from fastapi import Request, FastAPI


def _error_body(exception: AppError):
    return {
        'detail': exception.message,
        'status_code': exception.status_code,
        'name': exception.name
    }


def register_error_handlers(app: FastAPI):

    @app.exception_handler(ForbiddenError)
    async def forbidden_handler(request: Request, exception: ForbiddenError):
        return JSONResponse(status_code=403, content=_error_body(exception))

    @app.exception_handler(UnauthorizedError)
    async def forbidden_handler(request: Request, exception: UnauthorizedError):
        return JSONResponse(status_code=401, content=_error_body(exception))


