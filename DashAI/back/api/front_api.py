import os
from pathlib import Path

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse
from starlette.responses import FileResponse

from DashAI.back.containers import Container

router = APIRouter()


# React router should handle paths under /app, which are defined in index.html
@router.get("/app/{full_path:path}")
@inject
async def read_index(
    front_build_path=Depends(Provide[Container.config.FRONT_BUILD_PATH]),
):
    index_path = Path(f"{front_build_path}/index.html").absolute()
    return FileResponse(index_path)


# Serving static files
@router.get("/{file:path}")
@inject
async def serve_files(
    file: str,
    front_build_path=Depends(Provide[Container.config.FRONT_BUILD_PATH]),
):
    try:
        if file == "":
            return RedirectResponse(url="/app/")
        path = Path(f"{front_build_path}/{file}").absolute()

        os.stat(path)  # This checks if the file exists
        return FileResponse(path)  # You can't catch the exception here
    except FileNotFoundError:
        return RedirectResponse(url="/app/")
