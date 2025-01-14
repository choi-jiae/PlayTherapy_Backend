from fastapi import APIRouter, Depends, UploadFile, File
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import StreamingResponse
from dependency_injector.wiring import inject, Provide

from contents.container import Container
from contents.service.script import ScriptManagerService
from core.service.security import SecurityService

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/api/signin")


# 1. script(json) download
@router.get("/case/{case_id}/session/{session_id}/script", tags=["script"])
@inject
async def download_script(
    case_id: int,
    session_id: int,
    token: str = Depends(oauth2_scheme),
    script_manager_service: ScriptManagerService = Depends(
        Provide[Container.script_manager_service]
    ),
    security_service: SecurityService = Depends(Provide[Container.security_service]),
):
    payload = security_service.verify_token(token)
    script = await script_manager_service.download_script(
        case_id=case_id, session_id=session_id, user_id=payload.get("user_id")
    )
    return StreamingResponse(script, media_type="application/json")


# 2. script upload (s3에 업로드 / db에 url 갱신)
@router.post("/case/{case_id}/session/{session_id}/script", tags=["script"])
@inject
async def upload_script(
    case_id: int,
    session_id: int,
    script: UploadFile = File(...),
    token: str = Depends(oauth2_scheme),
    script_manager_service: ScriptManagerService = Depends(
        Provide[Container.script_manager_service]
    ),
    security_service: SecurityService = Depends(Provide[Container.security_service]),
):
    payload = security_service.verify_token(token)
    await script_manager_service.upload_script(
        script=script.file.read(),
        user_id=payload.get("user_id"),
        case_id=case_id,
        session_id=session_id,
    )
    return {"msg": "script upload success!"}
