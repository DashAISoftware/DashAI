import logging

from fastapi import APIRouter

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
async def get_dummy():
    return [{"name": "Real", "value": 42}, {"name": "Backend", "value": 24}]
