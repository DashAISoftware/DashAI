from fastapi import APIRouter

from DashAI.back.api.api_v1.endpoints.components import router as components
from DashAI.back.api.api_v1.endpoints.converters import router as converters
from DashAI.back.api.api_v1.endpoints.credentials import router as credentials
from DashAI.back.api.api_v1.endpoints.datafile import router as datafile_router
from DashAI.back.api.api_v1.endpoints.dataset_source import router as dataset_source
from DashAI.back.api.api_v1.endpoints.datasets import router as datasets
from DashAI.back.api.api_v1.endpoints.documents import router as documents
from DashAI.back.api.api_v1.endpoints.explainers import router as explainers
from DashAI.back.api.api_v1.endpoints.explorers import router as explorers
from DashAI.back.api.api_v1.endpoints.folders import router as folders
from DashAI.back.api.api_v1.endpoints.generative_process import (
    router as generative_process,
)
from DashAI.back.api.api_v1.endpoints.generative_session import (
    router as generative_session,
)
from DashAI.back.api.api_v1.endpoints.hardware import router as hardware
from DashAI.back.api.api_v1.endpoints.jobs import router as jobs
from DashAI.back.api.api_v1.endpoints.metrics import router as metrics
from DashAI.back.api.api_v1.endpoints.model_sessions import router as model_sessions
from DashAI.back.api.api_v1.endpoints.notebook import router as notebook
from DashAI.back.api.api_v1.endpoints.pipelines import router as pipelines
from DashAI.back.api.api_v1.endpoints.plugins import router as plugins
from DashAI.back.api.api_v1.endpoints.predict import router as predict
from DashAI.back.api.api_v1.endpoints.prompts import router as prompts
from DashAI.back.api.api_v1.endpoints.rag import router as rag
from DashAI.back.api.api_v1.endpoints.runs import router as runs
from DashAI.back.api.api_v1.endpoints.statistical_tests import (
    router as statistical_tests,
)

api_router_v1 = APIRouter()
api_router_v1.include_router(converters, prefix="/converter")
api_router_v1.include_router(components, prefix="/component")
api_router_v1.include_router(datasets, prefix="/dataset")
api_router_v1.include_router(documents, prefix="/document")
api_router_v1.include_router(model_sessions, prefix="/model-session")
api_router_v1.include_router(explainers, prefix="/explainer")
api_router_v1.include_router(explorers, prefix="/explorer")
api_router_v1.include_router(jobs, prefix="/job")
api_router_v1.include_router(runs, prefix="/run")
api_router_v1.include_router(predict, prefix="/predict")
api_router_v1.include_router(generative_session, prefix="/generative-session")
api_router_v1.include_router(generative_process, prefix="/generative-process")
api_router_v1.include_router(pipelines, prefix="/pipelines")
api_router_v1.include_router(plugins, prefix="/plugin")
api_router_v1.include_router(prompts, prefix="/prompt")
api_router_v1.include_router(notebook, prefix="/notebook")
api_router_v1.include_router(metrics, prefix="/metrics")
api_router_v1.include_router(hardware, prefix="/hardware")
api_router_v1.include_router(dataset_source, prefix="/dataset-source")
api_router_v1.include_router(datafile_router, prefix="/datafile")
api_router_v1.include_router(statistical_tests, prefix="/statistical-tests")
api_router_v1.include_router(folders, prefix="/folder")
api_router_v1.include_router(credentials, prefix="/credential")
api_router_v1.include_router(rag, prefix="/rag")
