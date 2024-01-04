import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from starlette.responses import FileResponse

from DashAI.back.api.api_v0.api import api_router_v0
from DashAI.back.api.api_v1.api import api_router_v1
from DashAI.back.core.config import settings

app = FastAPI(title="DashAI")
api_v0 = FastAPI(title="DashAI API v0")
api_v1 = FastAPI(title="DashAI API v1")

api_v0.include_router(api_router_v0)
api_v1.include_router(api_router_v1)

app.mount(settings.API_V0_STR, api_v0)
app.mount(settings.API_V1_STR, api_v1)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# React router should handle paths under /app, which are defined in index.html
@app.get("/app/{full_path:path}")
async def read_index():
    return FileResponse(f"{settings.FRONT_BUILD_PATH}/index.html")


# Serving static files
@app.get("/{file:path}")
async def serve_files(file: str):
    try:
        if file == "":
            return RedirectResponse(url="/app/")
        path = f"{settings.FRONT_BUILD_PATH}/{file}"
        os.stat(path)  # This checks if the file exists
        return FileResponse(path)  # You can't catch the exception here
    except FileNotFoundError:
        return RedirectResponse(url="/app/")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
