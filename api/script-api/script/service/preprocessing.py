import glob
import os
import re
from pathlib import Path
from typing import List

from moviepy.editor import VideoFileClip
from pydub import AudioSegment

import traceback

#from core.model.domain.session import Session
from core.model.domain.state_type import StateTypeEnum
from script.dto.preprocessing import PreprocessingResult
from core.repository.session import SessionRepository
from object.service.video import VideoService
from core.db.transaction import transaction_scope
from core.db.connection import ConnectionManager


class PreprocessingService:
    def __init__(self, video_split_output_path: str,
                 connection_manager: ConnectionManager,
                 session_repository: SessionRepository,
                 video_service: VideoService,
                 encoding_video_output: str):
        self.connection_manager = connection_manager
        self.video_split_output_path = video_split_output_path
        self.session_repository = session_repository
        self.video_service = video_service
        self.encoding_video_output = encoding_video_output
        self.encoding_dir = os.path.join(self.encoding_video_output, "encoding")
        self.download_dir = os.path.join(self.encoding_video_output, "download")

        if not os.path.exists(self.encoding_dir):
            try:
                os.makedirs(self.encoding_dir)
            except Exception as e:
                print(f"[PreprocessingService] directory error [{self.encoding_dir}]")

        if not os.path.exists(self.download_dir):
            try:
                os.makedirs(self.download_dir)
            except Exception as e:
                print(f"[PreprocessingService] directory error [{self.download_dir}]")

    def split_video(self, file_path: str) -> PreprocessingResult:
        path = Path(file_path)
        os.makedirs(self.video_split_output_path, exist_ok=True)
        current_file_output_path = os.path.join(self.video_split_output_path, path.stem)
        video_to_mp3_path = Path(os.path.join(current_file_output_path, "mp3"))
        split_mp3_path = Path(os.path.join(current_file_output_path, "split_mp3"))
        os.makedirs(current_file_output_path, exist_ok=True)
        os.makedirs(video_to_mp3_path, exist_ok=True)
        os.makedirs(split_mp3_path, exist_ok=True)
        mp3_path = self.__convert_video_to_mp3(video_path=path, output_path=video_to_mp3_path)
        self.__split_to_mp3(mp3_path=mp3_path, output_path=split_mp3_path)
        return PreprocessingResult(split_mp3_path=split_mp3_path)

    def __convert_video_to_mp3(self, video_path: Path, output_path: Path) -> Path:
        output_audio_path = Path(os.path.join(output_path.resolve(),
                                              f"{video_path.stem}.mp3"))

        video_clip = VideoFileClip(str(video_path.resolve()))

        audio_clip = video_clip.audio

        audio_clip.write_audiofile(output_audio_path, codec='mp3')

        audio_clip.close()
        video_clip.close()

        return output_audio_path

    def __split_to_mp3(self, mp3_path: Path, output_path: Path):
        audio = AudioSegment.from_mp3(str(mp3_path.resolve()))
        # 2분(120,000밀리초) 단위로 쪼개기
        two_minutes = 2 * 60 * 1000
        chunks = []

        for i in range(0, len(audio), two_minutes):
            chunk = audio[i:i + two_minutes]
            chunks.append(chunk)

        os.makedirs(output_path, exist_ok=True)
        for i, chunk in enumerate(chunks):
            output_mp3_path = os.path.join(output_path.resolve(), f"{mp3_path.stem}_part_{i + 1}.mp3")
            chunk.export(output_mp3_path, format='mp3')

    def download_and_upload_encode_video(self):
        try:
            db_session = self.connection_manager.make_session()
            update_session_start_state = False
            with transaction_scope(db_session) as tx_session:
                # 트랜젝션 열고
                # 한개 처리하는걸 보장한다.
                session = self.session_repository.get_by_encode_state_id(
                    state_id=StateTypeEnum.READY,
                    db_session=tx_session,
                )
                if session is None:
                    return
                session.encoding_state_id = int(StateTypeEnum.START)
                print(f"[PreprocessingService] session id:[{session.id}] start")
                update_session_start_state = self.session_repository.update(
                    session_id=session.id,
                    session=session,
                    db_session=tx_session
                )

            # 실제작업
            print(f"[PreprocessingService] session id:[{session.id}] upload and encoding")
            download_path = os.path.join(self.download_dir, session.origin_video_url)
            encoding_path = os.path.join(self.encoding_dir, session.origin_video_url)
            encoding_video_url = self.video_service.upload_encode_video(
                object_name=session.origin_video_url,
                file_name=download_path,
                encoded_path=encoding_path)

            session.encoding_video_url = encoding_video_url
            session.source_video_url = download_path
            session.encoding_state_id = int(StateTypeEnum.DONE)
            session.script_state_id = int(StateTypeEnum.READY)

            # 완료 처리
            db_session = self.connection_manager.make_session()
            with transaction_scope(db_session) as tx_session:
                ret = self.session_repository.update(
                    session_id=session.id,
                    session=session,
                    db_session=tx_session
                )

            print(f"[PreprocessingService] update result : [{ret}]")

            print(f"[PreprocessingService] session id:[{session.id}] complete\n"
                  f"object path : {encoding_video_url}\n"
                  f"local path : {download_path}")

        except Exception as e:
            print(e)

            traceback.print_exc()
            if update_session_start_state:

                session.encoding_state_id = int(StateTypeEnum.ERROR)
                self.session_repository.update(
                    session_id=session.id,
                    session=session,
                    db_session=tx_session
                )
