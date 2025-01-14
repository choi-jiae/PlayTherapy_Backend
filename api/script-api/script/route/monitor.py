from dependency_injector.wiring import inject

from fastapi import APIRouter

router = APIRouter()


@router.post("/liveness", tags=["Get"])
@inject
async def get_liveness():
    return "OK"


@router.post("/readiness", tags=["Get"])
@inject
async def get_readiness():
    return "OK"
