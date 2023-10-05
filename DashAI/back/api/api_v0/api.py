from fastapi import APIRouter

from DashAI.back.api.api_v0.endpoints import old_endpoints

api_router_v0 = APIRouter()
api_router_v0.include_router(old_endpoints.router)
