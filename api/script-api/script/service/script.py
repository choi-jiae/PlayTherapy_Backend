import json
from pathlib import Path
from typing import List
import os
import datetime
from core.db.connection import ConnectionManager
from core.db.transaction import transaction_scope
from core.model.domain.script import Script
from core.model.domain.session import Session
from core.model.domain.state_type import StateTypeEnum
from core.model.entity.session import SessionEntity
from core.repository.session import SessionRepository
from core.repository.state_type import StateTypeRepository
from object.service.script import ScriptService
from script.service.nonverbal import NonVerbalService
from script.service.preprocessing import PreprocessingService
from script.service.stt import SttService
import traceback
from pydub import AudioSegment


class ScriptGenerateService:
    def __init__(
            self,
            connection_manager: ConnectionManager,
            session_repository: SessionRepository,
            state_type_repository: StateTypeRepository,
            preprocessing_service: PreprocessingService,
            script_service: ScriptService,
            stt_service: SttService,
            non_verbal_service: NonVerbalService,
            external_volume_path: str,
    ):
        self.connection_manager = connection_manager
        self.session_repository = session_repository
        self.state_type_repository = state_type_repository
        self.preprocessing_service = preprocessing_service
        self.script_service = script_service
        self.stt_service = stt_service
        self.external_volume_path = external_volume_path
        self.non_verbal_service = non_verbal_service

    def run_from_db(self):
        current_time = datetime.datetime.now()
        formatted_time = current_time.strftime("%H:%M:%S")
        print(f"[ScriptService] run from db at {formatted_time}")
        target_session: Session = None
        update_session_start_state = False
        try:
            db_session = self.connection_manager.make_session()
            with transaction_scope(db_session) as tx_session:
                target_session: Session = (
                    self.session_repository.get_by_script_state_id(
                        state_id=StateTypeEnum.READY, db_session=db_session
                    )
                )

                if target_session is None:
                    print(f"[ScriptService] no target_session")
                    return

                if (
                        target_session.source_video_url is None
                        or target_session.source_video_url == ""
                ):
                    print(
                        f"[ScriptService] session id:[{target_session.id}] no target_session"
                    )
                    return

                print(
                    f"[ScriptService] session_id:[{target_session.id}] update target session state"
                )
                target_session.script_state_id = int(StateTypeEnum.START)
                update_session_start_state = self.session_repository.update(
                    session_id=target_session.id,
                    session=target_session,
                    db_session=tx_session,
                )

            local_video_path = target_session.source_video_url
            print(
                f"[ScriptService] session_id:[{target_session.id}] start preprocessing video {local_video_path}"
            )
            preprocessing_result = self.preprocessing_service.split_video(
                local_video_path
            )
            print(
                f"[ScriptService] session_id:[{target_session.id}] start gen script split path : {preprocessing_result.split_mp3_path}"
            )
            scripts = self.stt_service.run(
                audio_path=str(preprocessing_result.split_mp3_path.resolve())
            )
            new_file_name = f"{target_session.id}.json"
            save_file_path = os.path.join(self.external_volume_path, new_file_name)
            os.makedirs(self.external_volume_path, exist_ok=True)
            with open(save_file_path, "w") as f:
                json.dump(scripts.dict(), f, ensure_ascii=False)

            s3_file_path = os.path.dirname(target_session.origin_video_url)

            object_name = self.script_service.upload_script(
                file_name=save_file_path, file_path=s3_file_path
            )

            print(
                f"[ScriptService] session_id:[{target_session.id}] upload script {object_name}"
            )
            db_session = self.connection_manager.make_session()
            with transaction_scope(db_session) as tx_session:
                target_session.source_script_url = object_name
                target_session.script_state_id = int(StateTypeEnum.DONE)
                target_session.analyze_state_id = int(StateTypeEnum.READY)
                self.session_repository.update(
                    session_id=target_session.id,
                    session=target_session,
                    db_session=tx_session,
                )
        except Exception as e:
            print(traceback.format_exc())
            if update_session_start_state:
                db_session = self.connection_manager.make_session()
                with transaction_scope(db_session) as tx_session:
                    target_session.script_state_id = int(StateTypeEnum.ERROR)
                    self.session_repository.update(
                        session_id=target_session.id,
                        session=target_session,
                        db_session=tx_session,
                    )

    def run(self, path: str) -> Script:
        # mp4 to wav
        audio = AudioSegment.from_file(path, format="mp4")
        audio_path = self._rename_file_with_temp_and_change_extension(path, "wav")
        audio.export(audio_path, format="wav")
        script = self.stt_service.run(audio_path)
        script = self.non_verbal_service.run(Path(path), script)
        return script

    def _rename_file_with_temp_and_change_extension(self, file_path, new_extension):
        dir_name, base_name = os.path.split(file_path)
        file_name, old_extension = os.path.splitext(base_name)
        new_file_name = f"{file_name}_temp.{new_extension}"
        new_file_path = os.path.join(dir_name, new_file_name)
        return new_file_path
