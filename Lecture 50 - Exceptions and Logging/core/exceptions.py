from starlette import status


class AppError(Exception):
    def __init__(self, message, *, status_code: int | None = None):
        self.message = message
        self.status_code = status_code
        self.name = self.__class__.__name__

        super().__init__(message)


class ForbiddenError(AppError):
    """Returns status code 403"""
    # def __init__(self):
    #     self.status_code = status.HTTP_403_FORBIDDEN


class UnauthorizedError(AppError):
    """Returns status code 401"""
    pass



