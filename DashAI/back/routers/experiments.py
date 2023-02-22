from fastapi import APIRouter

from DashAI.back.routers.session_class import session_info

router = APIRouter()

# TODO To be rethinked. This is not working as intended.


@router.post("/experiment/")
async def run_experiment():
    main_task = session_info.task
    main_task.run_experiments(session_info.dataset)
    return {"message": "Experiment done"}


@router.get("/experiment/")
async def get_experiment():
    main_task = session_info.task
    return main_task.experimentResults


@router.delete("/experiment/")
async def delete_experiment():
    return {"message": "To be implemented"}


@router.put("/experiment/")
async def modify_experiment():
    return {"message": "To be implemented"}
