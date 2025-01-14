import io
import os
from functools import wraps
from object.repository.script import ScriptRepository
from object.exception import UploadFailed, DownloadFailed
from core.db.connection import ConnectionManager
from core.repository.session import SessionRepository
from core.repository.case import CaseRepository
from core.db.transaction import transaction_scope
from core.model.domain.state_type import StateTypeEnum
from contents.exception import CaseNotFound, SessionNotFound, ScriptNotFound


class ScriptManagerService:
    def __init__(
        self,
        script_repository: ScriptRepository,
        session_repository: SessionRepository,
        case_repository: CaseRepository,
        connection_manager: ConnectionManager,
    ):
        self.connection_manager = connection_manager
        self.script_repository = script_repository
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

    async def get_script_url(self, session_id):
        session = self.session_repository.get(session_id)
        if not session:
            raise SessionNotFound(session_id)
        return session.source_script_url

    async def update_script_url(self, session_id, script_url):
        db_session = self.connection_manager.make_session()
        with transaction_scope(db_session) as tx_session:
            session = self.session_repository.get(
                session_id=session_id, db_session=tx_session
            )
            session.source_script_url = script_url
            session.script_state_id = int(StateTypeEnum.DONE)
            res = self.session_repository.update(
                session_id=session_id,
                session=session,
                db_session=tx_session,
            )
            if not res:
                raise SessionNotFound(session_id)
        return script_url

    @check_case_exists
    async def download_script(self, case_id: int, session_id: int, user_id: int):
        script_url = await self.get_script_url(session_id)
        if not script_url:
            raise ScriptNotFound(session_id)

        script_body = self.script_repository.get_json(script_url)
        if not script_body:
            raise DownloadFailed(script_url)
        return io.BytesIO(script_body.read())

    @check_case_exists
    async def upload_script(
        self, script: bytes, user_id: int, case_id: int, session_id: int
    ):
        env = os.getenv("PHASE", "LOCAL")
        file_path = f"{env}/{case_id}/{session_id}"
        key_count = self.script_repository.get_object_list(file_path)["KeyCount"]
        object_name = f"{file_path}/script_v{key_count+1}.json"

        script_url = self.script_repository.upload_json(script, object_name)
        if not script_url:
            raise UploadFailed(object_name)

        await self.update_script_url(session_id, script_url)
