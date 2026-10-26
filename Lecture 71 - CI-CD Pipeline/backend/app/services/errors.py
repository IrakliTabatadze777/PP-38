class ServiceError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(code)
        self.code = code
        self.message = message


class NotAuthenticated(ServiceError):
    pass


class Forbidden(ServiceError):
    pass


class NotFound(ServiceError):
    pass


class Conflict(ServiceError):
    pass


class InvalidInput(ServiceError):
    pass


class OutOfRange(ServiceError):
    pass


class TooLarge(ServiceError):
    pass


class Unavailable(ServiceError):
    pass
