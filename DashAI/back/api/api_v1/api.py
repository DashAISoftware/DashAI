from fastapi import APIRouter

from DashAI.back.api.api_v1.endpoints import datasets

api_router_v1 = APIRouter()
api_router_v1.include_router(datasets.router, prefix="/dataset")
