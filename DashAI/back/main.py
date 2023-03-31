import os

from fastapi import FastAPI
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

#Load registries
task_registry = get_task_registry()
model_registry = get_model_registry()

# Move to testing
print(model_registry._models)

# print("Children query")
# print(reg_classes.get_class_children("BaseTask"))

# print("Children query II")
# print(reg_classes.get_class_children("TabularClassificationModel"))

# print("Children query III")
# print(reg_classes.get_class_children("SklearnLikeModel"))

# print("Children query IV")
# print(reg_classes.get_class_children("BaseModel"))

for task in task_registry._tasks.values(): # SVM no debería aparecer aquí
    print(task.name)
    print(task.compatible_models)

from importlib_metadata import entry_points
@app.get("/update_registry")
async def update_registry():
    discovered_plugins = entry_points(group='dashai.plugins')
    for plugin in discovered_plugins:
        f = plugin.load()
        model_registry.register_model(f())

@app.get("/tasks")
async def get_tasks():
    for task in task_registry._tasks.values(): # SVM no debería aparecer aquí
        print(task.name)
        print(task.compatible_models)

# React router should handle paths under /app, which are defined in index.html
@app.get("/app/{full_path:path}")
async def read_index():
    return FileResponse(f"{settings.FRONT_BUILD_PATH}/index.html")

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
