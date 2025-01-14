from io import BytesIO
from fastapi import APIRouter, Depends, File, UploadFile, BackgroundTasks
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.security import OAuth2PasswordBearer
from dependency_injector.wiring import inject, Provide

from contents.container import Container
from contents.service.video import VideoManagerService
from core.service.security import SecurityService

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/api/signin")


# 1. encoded video download (s3에서 바로 영상 스트리밍)
@router.get("/case/{case_id}/session/{session_id}/video", tags=["video"])
@inject
async def download_video(
    case_id: int,
    session_id: int,
    token: str = Depends(oauth2_scheme),
    video_manager_service: VideoManagerService = Depends(
        Provide[Container.video_manager_service]
    ),
    security_service: SecurityService = Depends(Provide[Container.security_service]),
):
    payload = security_service.verify_token(token)
    streaming_body = await video_manager_service.download_video(case_id=case_id, session_id=session_id, user_id=payload.get("user_id"))
    return StreamingResponse(streaming_body, media_type="video/mp4")


# 2. origin video upload (s3로 바로 upload -> JSON response 201)
@router.post("/case/{case_id}/session/{session_id}/video", tags=["video"])
@inject
async def upload_video(
    case_id: int,
    session_id: int,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    token: str = Depends(oauth2_scheme),
    video_manager_service: VideoManagerService = Depends(
        Provide[Container.video_manager_service]
    ),
    security_service: SecurityService = Depends(Provide[Container.security_service]),
):
    payload = security_service.verify_token(token)

    file_contents = await file.read()
    file_obj = BytesIO(file_contents)  # 메모리에 파일을 저장하는 BytesIO 객체 생성

    background_tasks.add_task(
        video_manager_service.upload_video_obj,
        case_id=case_id,
        session_id=session_id,
        user_id=payload.get("user_id"),
        file_obj=file_obj,
        filename=file.filename,
    )

    return JSONResponse(status_code=201, content={"msg": "s3 upload start!"})

# 3. presigned url 생성 (s3에 파일 업로드할 수 있는 url 생성)
@router.get("/case/{case_id}/session/{session_id}/video/presigned-url")
@inject
async def get_presigned_url(
    case_id: int,
    session_id: int,
    token: str = Depends(oauth2_scheme),
    video_manager_service: VideoManagerService = Depends(
        Provide[Container.video_manager_service]
    ),
    security_service: SecurityService = Depends(Provide[Container.security_service]),
):
    payload = security_service.verify_token(token)
    presigned_url, file_path = await video_manager_service.get_presigned_url(
        case_id=case_id, 
        session_id=session_id,
        user_id=payload.get("user_id")
    )
    return JSONResponse(status_code=200, content={"presigned_url": presigned_url, "file_path": file_path})