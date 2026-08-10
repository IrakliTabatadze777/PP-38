from fastapi import FastAPI
from routers import user_router, product_router, user_router_v2

app = FastAPI()

app.include_router(user_router, prefix='/api/v1')
app.include_router(product_router, prefix='/api/v1')
app.include_router(user_router_v2, prefix='/api/v2')