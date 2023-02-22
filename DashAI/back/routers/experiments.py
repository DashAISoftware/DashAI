from fastapi import APIRouter

from DashAI.back.routers.session_class import session_info

router = APIRouter()

# TODO To be rethinked. This is not working as intended.

@router.post("/experiment/run/{session_id}")
async def run_experiment():
    main_task = session_info.task
    main_task.run_experiments(session_info.dataset)
    return 0


@router.get("/experiment/results/{session_id}")
async def get_results():
    main_task = session_info.task
    return main_task.experimentResults
