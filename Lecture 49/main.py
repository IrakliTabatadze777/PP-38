from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from routers import user_router, product_router, order_router, user_router_v2
from core.middlewares import CorrelationIDMiddleware
import logging


logger = logging.getLogger('uvicorn.access')
app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:3000', 'http://127.0.0.1:3000'],
    # allow_origins=["*"],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.add_middleware(CorrelationIDMiddleware)

@app.middleware('http')
async def log_request(request: Request, call_next):
    logger.info(f'Incoming request: {request.url}, {request.method}')

    start_time = datetime.now()
    response = await call_next(request)

    end_time = datetime.now()

    response.headers['X-Processing-Time'] = str(end_time - start_time)
    response.headers['X-Correlation-ID'] = request.state['X-Correlation-ID']

    logger.info(f'Response status: {response.status_code}')
    return response


app.include_router(user_router, prefix='/api/v1')
app.include_router(product_router, prefix='/api/v1')
app.include_router(order_router, prefix='/api/v1')
app.include_router(user_router_v2, prefix='/api/v2')