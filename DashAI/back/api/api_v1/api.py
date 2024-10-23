from fastapi import APIRouter

from DashAI.back.api.api_v1.endpoints import (
    components,
    datasets,
    experiments,
    explainers,
    image_generation,
    jobs,
    predict,
    runs,
    llm,
    llm_generation,
)

api_router_v1 = APIRouter()
api_router_v1.include_router(components.router, prefix="/component")
api_router_v1.include_router(datasets.router, prefix="/dataset")
api_router_v1.include_router(experiments.router, prefix="/experiment")
api_router_v1.include_router(explainers.router, prefix="/explainer")
api_router_v1.include_router(jobs.router, prefix="/job")
api_router_v1.include_router(runs.router, prefix="/run")
api_router_v1.include_router(predict.router, prefix="/predict")
api_router_v1.include_router(image_generation.router, prefix="/image-generation")
api_router_v1.include_router(llm.router, prefix="/llm")
api_router_v1.include_router(llm_generation.router, prefix="/llm-generation")
