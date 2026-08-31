from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from fastapi import Request, Response


class CorrelationIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        import uuid

        correlation_id = str(uuid.uuid4())

        request.state['X-Correlation-ID'] = correlation_id

        response = await call_next(request)

        return response
