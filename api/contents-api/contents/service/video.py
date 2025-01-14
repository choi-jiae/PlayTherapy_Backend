import os
from functools import wraps
from typing import IO
from object.repository.video import VideoRepository
from object.exception import UploadFailed, DownloadFailed
from core.db.connection import ConnectionManager
from core.repository.session import SessionRepository
from core.repository.case import CaseRepository
from core.db.transaction import transaction_scope
from core.model.domain.state_type import StateTypeEnum
from contents.exception import CaseNotFound, SessionNotFound, VideoNotFound


class VideoManagerService:
    def __init__(
        self,
        video_repository: VideoRepository,
        session_repository: SessionRepository,
        case_repository: CaseRepository,
        connection_manager: ConnectionManager,
    ):
        self.connection_manager = connection_manager
        self.video_repository = video_repository
        self.session_repository = session_repository
        self.case_repository = case_repository

    def check_case_exists(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            case_id = kwargs.get("case_id")
            user_id = kwargs.get("user_id")
            case = self.case_repository.get(case_id=case_id, user_id=user_id)
            if not case:
                raise CaseNotFound(case_id)
            return await func(self, *args, **kwargs)

        return wrapper

    async def get_encoded_video_url(self, session_id: int):
        session = self.session_repository.get(session_id)
        if not session:
            raise SessionNotFound(session_id)
        return session.encoding_video_url

    def get_origin_video_url(self, session_id: int):
        session = self.session_repository.get(session_id)
        if not session:
            raise SessionNotFound(session_id)
        return session.origin_video_url

    def get_source_video_url(self, session_id: int):
        session = self.session_repository.get(session_id)
        if not session:
            raise SessionNotFound(session_id)
        return session.source_video_url

    async def update_origin_video_url(self, session_id, origin_video_url: str):
        db_session = self.connection_manager.make_session()

        with transaction_scope(db_session) as tx_session:
            session = self.session_repository.get(
                session_id=session_id, db_session=tx_session
            )
            session.origin_video_url = origin_video_url
            session.encoding_state_id = int(StateTypeEnum.READY)
            res = self.session_repository.update(
                session_id=session_id,
                session=session,
                db_session=tx_session,
            )
            if not res:
                raise SessionNotFound(session_id)
        return origin_video_url

    @check_case_exists
    async def download_video(self, case_id: int, session_id: int, user_id: int):
        encoded_video_url = await self.get_encoded_video_url(session_id)
        if not encoded_video_url:
            raise VideoNotFound(session_id)
        video = self.video_repository.get_object(encoded_video_url)
        if not video:
            raise DownloadFailed(encoded_video_url)
        return video["Body"]

    @check_case_exists
    async def upload_video_obj(
        self,
        case_id: int,
        session_id: int,
        user_id: int,
        file_obj: IO[bytes],
        filename: str,
    ):
        env = os.getenv("PHASE", "LOCAL")
        file_path = f"{env}/{case_id}/{session_id}/"
        url_result = self.video_repository.upload_obj(file_obj, file_path + filename)
        if not url_result:
            raise UploadFailed(filename)
        updated_res = await self.update_origin_video_url(session_id, url_result)
        return updated_res

    @check_case_exists
    async def get_presigned_url(
        self,
        case_id: int,
        session_id: int,
        user_id: int,
    ):
        env = os.getenv("PHASE", "LOCAL")
        file_path = f"{env}/{case_id}/{session_id}/video.mp4"
        url_result = self.video_repository.get_presigned_url(file_path)

        if not url_result:
            raise UploadFailed(session_id)
        return url_result, file_path