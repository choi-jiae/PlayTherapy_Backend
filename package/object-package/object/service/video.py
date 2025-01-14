from object.repository.video import VideoRepository
from moviepy.editor import VideoFileClip
from object.exception import UploadFailed
import os

class VideoService:
    def __init__(self, video_repository: VideoRepository):
        self.video_repository = video_repository

    def upload_origin_video(self, file_name: str, object_name: str):
        url_result = self.video_repository.upload(file_name, object_name)
        if not url_result:
            raise UploadFailed(file_name)
        return url_result
    
    def upload_encode_video(
        self, object_name: str, file_name: str, encoded_path: str
    ):
        encoded_path = self.download_and_encode_video(
            object_name, file_name, encoded_path
        )

        encoded_video_url = object_name.split('/')
        encoded_video_url[-1] = "encoded_"+encoded_video_url[-1]

        url_result = self.video_repository.upload(
            encoded_path, '/'.join(encoded_video_url)
        )
        if not url_result:
            raise UploadFailed(encoded_path)
        return url_result
    
        
    def download_and_encode_video(self, object_name: str, file_name: str, encoded_path: str):

        try:
            print(f"Downloading video: {object_name}")
            downloaded_file = self.video_repository.download(object_name, file_name)

            if downloaded_file:
                print(f"[ObjectService] start encoding: '{file_name}'.")
                print(f"Encoding video: {object_name}")
                encoded_path = self.encode_video(downloaded_file, encoded_path)
            else:
                print(f"[ObjectService] no download file: '{file_name}'.")
                return None
        except Exception as e:
            print(f"Cannot encode video: '{object_name}'. Error: {e}")
            return None
        
    def encode_video(self, file_name: str, encoded_path: str):
        try:
            file_dir = os.path.dirname(encoded_path)
            if not os.path.exists(file_dir):
                os.makedirs(file_dir, exist_ok=True)

            clip = VideoFileClip(file_name)
            clip.write_videofile(
                encoded_path,
                fps=24,
                threads=os.cpu_count()-1,
                codec="libx264",
                bitrate="96k",
                audio_codec="aac",
                logger=None,
                audio_bitrate="72k",
                preset="ultrafast",
            )
            print(f"[ObjectService] end encoding: '{encoded_path}'.")
            return encoded_path
        except Exception as e:
            print(f"Cannot encode video: '{file_name}'. Error: {e}")
            return None